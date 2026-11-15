from datetime import date, timedelta

from fastapi.testclient import TestClient

from app.auth import Role, email_lookup_hash
from app.db import get_db
from app.main import app
from app.models import Cart, CartItem, InventoryLot, Product, ShoppingSession, User
from app.services.shopping_list import add_recipe_to_list, note_text


def _id(database, sku):
    return database.query(Product).filter_by(sku=sku).one().id


def _recipe(database, *skus, extra=()):
    ingredients = [{"name": sku, "product_id": _id(database, sku)} for sku in skus]
    return {"title": "Test dish", "ingredients": [*ingredients, *extra], "steps": ["Cook."]}


def _put_in_cart(database, user, sku):
    session = ShoppingSession(Shopping_Session_Token="synthetic-diff", client_id=user.id)
    database.add(session)
    database.flush()
    cart = Cart(session_id=session.id)
    database.add(cart)
    database.flush()
    database.add(CartItem(cart_id=cart.id, product_id=_id(database, sku), quantity=1))
    database.commit()


def _sell_out(database, sku):
    for lot in database.query(InventoryLot).filter_by(product_id=_id(database, sku)):
        lot.quantity = 0
    database.commit()


def test_diff_skips_cart_and_listed_items_and_adds_the_rest_with_locations(database, logged_in_client):
    user = logged_in_client(Role.CLIENT).user
    _put_in_cart(database, user, "SYN-OATS-001")
    recipe = _recipe(database, "SYN-OATS-001", "SYN-BEANS-001")

    first = add_recipe_to_list(database, user, recipe)
    again = add_recipe_to_list(database, user, recipe)

    assert first["in_cart"] == 1 and first["already_on_list"] == 0
    assert [a["name"] for a in first["added"]] == ["Synthetic Black Beans"]
    assert first["added"][0]["location"]["aisle"]
    assert again["added"] == [] and again["already_on_list"] == 1


def test_restricted_ingredient_is_never_added_and_comes_back_with_reason(database, logged_in_client):
    # The seeded active client includes a child with a nut allergy, so the nut crackers are Restricted.
    user = database.query(User).filter_by(email_hash=email_lookup_hash("client.active@example.test")).one()
    result = add_recipe_to_list(database, user, _recipe(database, "SYN-CRACK-001", "SYN-OATS-001"))

    assert [b["name"] for b in result["blocked"]] == ["SYN-CRACK-001"]
    assert result["blocked"][0]["not_for"]
    assert [a["name"] for a in result["added"]] == ["Synthetic Rolled Oats"]


def test_out_of_stock_or_unknown_becomes_a_plain_note(database, logged_in_client):
    user = logged_in_client(Role.CLIENT).user
    _sell_out(database, "SYN-BEANS-001")
    recipe = _recipe(database, "SYN-BEANS-001", extra=[{"name": "salt", "product_id": None}])

    result = add_recipe_to_list(database, user, recipe)

    assert [a["name"] for a in result["added"]] == [note_text("SYN-BEANS-001"), "salt"]
    assert all(a["location"] is None for a in result["added"])


def test_endpoint_and_save_both_apply_the_diff(database, logged_in_client):
    login = logged_in_client(Role.CLIENT)
    recipe = _recipe(database, "SYN-OATS-001")
    app.dependency_overrides[get_db] = lambda: database
    try:
        api = TestClient(app)
        saved = api.post("/me/recipes", json=recipe, cookies=login.cookies)
        listed = api.post("/shopping-list/from-recipe", json={"recipe": recipe}, cookies=login.cookies)
    finally:
        app.dependency_overrides.clear()
    assert saved.status_code == 201 and len(saved.json()["list"]["added"]) == 1
    assert listed.json()["added"] == [] and listed.json()["already_on_list"] == 1
