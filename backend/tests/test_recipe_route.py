import json

import pytest
from fastapi.testclient import TestClient

from app.ai.orchestrator import AIOrchestrationError
from app.ai.provider import AIProvider, AITask
from app.auth import Role
from app.db import get_db
from app.main import app
from app.models import AIRequest, CartItem, Client, Product, ShoppingSession
from app.services.cart import get_or_create_cart


def test_recipe_route_falls_back_when_provider_is_unavailable(database, logged_in_client):
    user = logged_in_client(Role.CLIENT).user
    database.add(
        ShoppingSession(
            Shopping_Session_Token="synthetic-recipe-session",
            client_id=user.id,
        )
    )
    database.commit()
    app.dependency_overrides[get_db] = lambda: database
    try:
        response = TestClient(app).post(
            "/recipes",
            cookies=logged_in_client(Role.CLIENT).cookies,
        )
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json()["used_fallback"] is True


class FakeProvider(AIProvider):
    name = "fake"

    def generate_json(self, task, manifest):
        first, second = manifest.items[0], manifest.items[1]
        if task is AITask.RECIPES:
            ingredient = {"name": first.name, "product_id": first.index}
            recipe = {"title": "Synthetic bowl", "ingredients": [ingredient], "steps": ["Mix."]}
            return {"recipes": [recipe]}
        return {"items": [{"product_id": second.index, "reason": "Adds flavor."}]}


@pytest.fixture
def nut_allergy_cart(database, logged_in_client):
    """A client with a Nut Allergy whose cart holds one allowed and one Restricted item."""
    user = logged_in_client(Role.CLIENT).user
    database.get(Client, user.id).dietary_profile.restrictions = json.dumps(["Nut Allergy"])
    session = ShoppingSession(Shopping_Session_Token="synthetic-ai-session", client_id=user.id)
    database.add(session)
    database.commit()
    cart = get_or_create_cart(database, session)
    by_sku = {p.sku: p for p in database.query(Product)}
    for sku in ("SYN-OATS-001", "SYN-CRACK-001"):
        database.add(CartItem(cart_id=cart.id, product_id=by_sku[sku].id, quantity=1))
    database.commit()
    return by_sku["SYN-CRACK-001"].id, by_sku["SYN-OATS-001"].id


def post_recipes(database, logged_in_client):
    app.dependency_overrides[get_db] = lambda: database
    try:
        return TestClient(app, cookies=logged_in_client(Role.CLIENT).cookies).post("/recipes")
    finally:
        app.dependency_overrides.clear()


def ingredient_ids(body):
    return {i["product_id"] for recipe in body["recipes"] for i in recipe["ingredients"]}


def test_recipe_route_fallback_is_logged_and_never_uses_restricted_items(
    database, logged_in_client, nut_allergy_cart, monkeypatch
):
    restricted_id, oats_id = nut_allergy_cart

    def down(*args, **kwargs):
        raise AIOrchestrationError("provider down")

    monkeypatch.setattr("app.routes.recipes.run_ai_task", down)
    body = post_recipes(database, logged_in_client).json()

    assert body["used_fallback"] is True and body["missing_ingredients"] == []
    assert ingredient_ids(body) == {oats_id}
    request = database.query(AIRequest).one()
    assert (request.kind, request.used_fallback, request.valid) == ("recipes", True, False)


def test_recipe_route_returns_guarded_recipes_and_missing_ingredient_locations(
    database, logged_in_client, nut_allergy_cart, monkeypatch
):
    restricted_id, _ = nut_allergy_cart
    monkeypatch.setattr("app.ai.orchestrator.get_provider", lambda: FakeProvider())
    body = post_recipes(database, logged_in_client).json()

    assert body["used_fallback"] is False
    assert restricted_id not in ingredient_ids(body)
    [missing] = body["missing_ingredients"]
    assert missing["product_id"] != restricted_id
    assert set(missing["location"]) == {"aisle", "shelf", "bin"}
    assert database.query(AIRequest).one().model == "fake"


def test_recipe_route_falls_back_when_ai_recipe_has_unlisted_ingredient(
    database, logged_in_client, nut_allergy_cart, monkeypatch
):
    class PantryOnly(FakeProvider):
        def generate_json(self, task, manifest):
            salt = {"name": "Salt", "product_id": None}
            return {"recipes": [{"title": "Pantry", "ingredients": [salt], "steps": ["Mix."]}]}

    monkeypatch.setattr("app.ai.orchestrator.get_provider", lambda: PantryOnly())
    assert post_recipes(database, logged_in_client).json()["used_fallback"] is True
