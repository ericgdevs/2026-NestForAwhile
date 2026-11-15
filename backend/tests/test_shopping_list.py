from fastapi.testclient import TestClient

from app.auth import Role
from app.db import get_db
from app.main import app
from app.models import Cart, CartItem, Product, ShoppingSession
from app.services.shopping_list import split_lines


def _api(database):
    app.dependency_overrides[get_db] = lambda: database
    return TestClient(app)


def test_split_lines_drops_bullets_and_counts():
    assert split_lines("- 2 cans black beans\n• oats, milk;  \n3x rice") == [
        "cans black beans",
        "oats",
        "milk",
        "rice",
    ]


def test_parse_matches_stock_with_location_and_marks_unknown(database, logged_in_client):
    cookies = logged_in_client(Role.CLIENT).cookies
    try:
        body = (
            _api(database)
            .post(
                "/shopping-list/parse",
                json={"text": "2 cans black beans\nunicorn glitter"},
                cookies=cookies,
            )
            .json()
        )
    finally:
        app.dependency_overrides.clear()
    beans, unknown = body["lines"]
    assert "black beans" in beans["name"].lower() and beans["location"]["aisle"]
    assert unknown["product_id"] is None


def test_photo_parse_says_so_when_no_vision_model(database, logged_in_client, monkeypatch):
    monkeypatch.delenv("OLLAMA_VISION_MODEL", raising=False)
    monkeypatch.setenv("AI_PROVIDER", "ollama")
    try:
        response = _api(database).post(
            "/shopping-list/parse",
            json={"image_base64": "aGVsbG8="},
            cookies=logged_in_client(Role.CLIENT).cookies,
        )
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 503
    assert "type your list" in response.json()["detail"]


def test_list_sorts_by_aisle_tags_recipes_and_tick_adds_to_cart(database, logged_in_client):
    login = logged_in_client(Role.CLIENT)
    session = ShoppingSession(Shopping_Session_Token="synthetic-list", client_id=login.user.id)
    database.add(session)
    database.commit()
    oats = database.query(Product).filter_by(sku="SYN-OATS-001").one()
    recipe = {"title": "Oat porridge", "ingredients": [], "steps": ["Simmer."]}
    try:
        api = _api(database)
        api.post("/shopping-list", json={"items": [{"text": "black beans"}]}, cookies=login.cookies)
        listed = api.post(
            "/shopping-list",
            json={"items": [{"text": "oats", "product_id": oats.id}], "recipe": recipe},
            cookies=login.cookies,
        ).json()["items"]
        oats_line = next(line for line in listed if line["product_id"] == oats.id)
        api.patch(f"/shopping-list/{oats_line['id']}", json={"ticked": True}, cookies=login.cookies)
        api.patch(f"/shopping-list/{oats_line['id']}", json={"ticked": True}, cookies=login.cookies)
        other = api.delete(
            f"/shopping-list/{oats_line['id']}",
            cookies=logged_in_client(Role.VOLUNTEER).cookies,
        )
    finally:
        app.dependency_overrides.clear()

    aisles = [line["location"]["aisle"] for line in listed]
    assert aisles == sorted(aisles)
    assert oats_line["source"] == "recipe" and [r["title"] for r in oats_line["recipes"]] == [
        "Oat porridge"
    ]
    assert next(line for line in listed if line["product_id"] != oats.id)["source"] == "you"
    cart = database.query(Cart).filter_by(session_id=session.id).one()
    assert (
        database.query(CartItem).filter_by(cart_id=cart.id, product_id=oats.id).one().quantity == 1
    )
    assert other.status_code == 403


def test_same_item_twice_is_one_line_tagged_with_every_recipe(database, logged_in_client):
    cookies = logged_in_client(Role.CLIENT).cookies
    beans = database.query(Product).filter_by(sku="SYN-BEANS-001").one()
    tacos = {"title": "Bean tacos", "ingredients": [], "steps": ["Warm."]}
    chili = {"title": "Bean chili", "ingredients": [], "steps": ["Simmer."]}
    try:
        api = _api(database)
        for recipe in (tacos, chili, tacos):
            api.post(
                "/shopping-list",
                json={"items": [{"text": "beans", "product_id": beans.id}], "recipe": recipe},
                cookies=cookies,
            )
        api.post(
            "/shopping-list",
            json={"items": [{"text": "black beans", "product_id": beans.id}]},
            cookies=cookies,
        )
        api.post("/shopping-list", json={"items": [{"text": "Unicorn glitter"}]}, cookies=cookies)
        lines = api.post(
            "/shopping-list", json={"items": [{"text": "unicorn glitter"}]}, cookies=cookies
        ).json()["items"]
    finally:
        app.dependency_overrides.clear()

    bean_lines = [line for line in lines if line["product_id"] == beans.id]
    assert len(bean_lines) == 1
    assert [r["title"] for r in bean_lines[0]["recipes"]] == ["Bean tacos", "Bean chili"]
    assert bean_lines[0]["source"] == "you"  # also added by hand
    assert len([line for line in lines if line["product_id"] is None]) == 1
