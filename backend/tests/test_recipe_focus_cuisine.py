import pytest
from fastapi.testclient import TestClient

from app.ai.orchestrator import AIOrchestrationError
from app.ai.provider import AIProvider, AITask
from app.ai.schemas import RecipeOutput
from app.auth import Role
from app.db import get_db
from app.main import app
from app.models import Product, ShoppingSession


@pytest.fixture
def shopping(database, logged_in_client):
    login = logged_in_client(Role.CLIENT)
    database.add(ShoppingSession(Shopping_Session_Token="synthetic-focus", client_id=login.user.id))
    database.commit()
    return {p.sku: p.id for p in database.query(Product)}, login.cookies


def _post(database, cookies, body):
    app.dependency_overrides[get_db] = lambda: database
    try:
        return TestClient(app, cookies=cookies).post("/recipes", json=body).json()
    finally:
        app.dependency_overrides.clear()


def _ai_down(monkeypatch):
    def down(*args, **kwargs):
        raise AIOrchestrationError("provider down")

    monkeypatch.setattr("app.routes.recipes.run_ai_task", down)


def test_fallback_recipes_use_the_scanned_item_and_filter_by_cuisine(
    database, shopping, monkeypatch
):
    ids, cookies = shopping
    _ai_down(monkeypatch)
    every = _post(database, cookies, {"scanned_product_id": ids["SYN-OATS-001"]})
    mexican = _post(
        database, cookies, {"scanned_product_id": ids["SYN-OATS-001"], "cuisine": "mexican"}
    )

    assert {r["cuisine"] for r in every["recipes"]} == {"American", "Asian", "Mexican"}
    assert [r["cuisine"] for r in mexican["recipes"]] == ["Mexican"]
    oats = mexican["recipes"][0]["ingredients"][0]
    assert oats["product_id"] == ids["SYN-OATS-001"]
    assert oats["in_cart_or_stock"] is True and oats["location"]["aisle"]


def test_no_recipes_for_an_item_that_is_unsafe_for_any_member(database, shopping, monkeypatch):
    ids, cookies = shopping
    _ai_down(monkeypatch)  # Little one has a nut allergy; crackers contain tree nuts
    body = _post(database, cookies, {"scanned_product_id": ids["SYN-CRACK-001"]})
    assert body["recipes"] == []


class CuisineProvider(AIProvider):
    name = "fake-cuisines"

    def generate_json(self, task, manifest, feedback=None):
        if task is not AITask.RECIPES:
            return {"items": []}
        focus = manifest.focus_index
        other = next(item.index for item in manifest.items if item.index != focus)

        def recipe(title, cuisine, index):
            ingredient = {"name": manifest.items[index].name, "product_id": index}
            return {
                "title": title,
                "cuisine": cuisine,
                "ingredients": [ingredient],
                "steps": ["Cook."],
            }

        return {
            "recipes": [
                recipe("Uses scan", "Italian", focus),
                recipe("Ignores scan", "Thai", other),
            ]
        }


def test_ai_recipes_must_use_the_scanned_item(database, shopping, monkeypatch):
    ids, cookies = shopping
    monkeypatch.setattr("app.ai.orchestrator.get_provider", lambda: CuisineProvider())
    body = _post(database, cookies, {"scanned_product_id": ids["SYN-OATS-001"]})

    assert body["used_fallback"] is False
    assert [(r["title"], r["cuisine"]) for r in body["recipes"]] == [("Uses scan", "Italian")]


def test_recipe_schema_allows_cuisine_and_at_most_six_recipes():
    one = {
        "title": "T",
        "cuisine": "Italian",
        "ingredients": [{"name": "x", "product_id": 0}],
        "steps": ["s"],
    }
    assert RecipeOutput(recipes=[one] * 6).recipes[0].cuisine == "Italian"
    with pytest.raises(ValueError):
        RecipeOutput(recipes=[one] * 7)


class SixRecipeProvider(AIProvider):
    """Six recipes; one uses a non-stock (pantry) ingredient the guard must drop."""

    name = "fake-six"
    seen: list = []

    def generate_json(self, task, manifest, feedback=None):
        SixRecipeProvider.seen.append(manifest)
        if task is not AITask.RECIPES:
            return {"items": []}
        first = manifest.items[0]

        def recipe(n, product_id):
            ingredient = {
                "name": first.name if product_id is not None else "Salt",
                "product_id": product_id,
            }
            return {
                "title": f"Recipe {n}",
                "cuisine": "Test",
                "ingredients": [ingredient],
                "steps": ["Cook."],
            }

        return {"recipes": [recipe(n, first.index) for n in range(5)] + [recipe(5, None)]}


def test_all_six_recipes_are_guarded_with_every_members_restrictions(
    database, shopping, monkeypatch
):
    ids, cookies = shopping
    SixRecipeProvider.seen = []
    monkeypatch.setattr("app.ai.orchestrator.get_provider", lambda: SixRecipeProvider())
    body = _post(database, cookies, {})

    manifest = SixRecipeProvider.seen[0]
    # Person 1 is Low Sodium and Little one has a Nut Allergy: the AI sees the union of both...
    assert sorted(manifest.restrictions) == ["Low Sodium", "Nut Allergy"]
    # ...and never sees a product restricted for either member.
    assert "Synthetic Nut Crackers" not in {item.name for item in manifest.items}
    # Every one of the six recipes went through the guard: the pantry-only one was dropped.
    assert [r["title"] for r in body["recipes"]] == [f"Recipe {n}" for n in range(5)]
    assert ids["SYN-CRACK-001"] not in {
        i["product_id"] for r in body["recipes"] for i in r["ingredients"]
    }
