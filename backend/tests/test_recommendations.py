from fastapi.testclient import TestClient

from app.auth import Role
from app.db import get_db
from app.main import app
from app.models import (
    Cart,
    CartItem,
    Checkout,
    CheckoutItem,
    Client,
    InventoryLot,
    Product,
    ShoppingListItem,
    ShoppingSession,
)
from app.services.recommendations import POPULAR_COUNT


def test_recommendations_scale_to_household_and_exclude_restricted(database, logged_in_client):
    app.dependency_overrides[get_db] = lambda: database
    try:
        response = TestClient(app).get(
            "/recommendations",
            cookies=logged_in_client(Role.CLIENT).cookies,
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    items = response.json()
    assert items
    assert all(item["status"] != "Restricted" for item in items)
    assert all(item["quantity"] == 2 for item in items)
    assert all(item["rationale"] for item in items)


def test_portions_count_children_as_half():
    from app.services.recommendations import household_portions

    adult, child = {"age": 40}, {"age": 7}
    assert household_portions([adult, child], 2) == 2  # 1.5 rounds up
    assert household_portions([adult, adult, child, child], 4) == 3
    assert household_portions([{"age": None}], 1) == 1
    assert household_portions([], 3) == 3


def test_saved_recipe_items_come_first_with_a_reason(database, logged_in_client):
    from app.models import Product, SavedRecipe

    login = logged_in_client(Role.CLIENT)
    beans = _good_matches(database, login, 12)[-1]  # a good match that is not already first
    database.add(
        SavedRecipe(
            client_id=login.user.id,
            title="Bean tacos",
            recipe={
                "title": "Bean tacos",
                "ingredients": [{"name": "beans", "product_id": beans.id}],
                "steps": ["Cook."],
            },
        )
    )
    database.commit()
    app.dependency_overrides[get_db] = lambda: database
    try:
        picks = TestClient(app).get("/recommendations", cookies=login.cookies).json()
    finally:
        app.dependency_overrides.clear()
    assert picks[0]["product_id"] == beans.id
    assert "recipe you saved" in picks[0]["rationale"]


# --- picks come from the client's own history, saved recipes and list; fallback is popularity ---
def _recommend(database, login):
    app.dependency_overrides[get_db] = lambda: database
    try:
        return TestClient(app).get("/recommendations", cookies=login.cookies).json()
    finally:
        app.dependency_overrides.clear()


def _product(database, sku):
    return database.query(Product).filter_by(sku=sku).one()


def _good_matches(database, login, count):
    """The first products a history-free client is recommended: all clean Good matches."""
    return [database.get(Product, pick["product_id"]) for pick in _recommend(database, login)[:count]]


def _checkout(database, client_id, product, quantity):
    """A completed checkout for a client (synthetic)."""
    lot = database.query(InventoryLot).filter_by(product_id=product.id).first()
    session = ShoppingSession(
        Shopping_Session_Token=f"synthetic-{client_id}-{product.id}-{quantity}",
        client_id=client_id,
        status="completed",
    )
    database.add(session)
    database.flush()
    checkout = Checkout(
        session_id=session.id, validated_by=client_id, status="completed", total_lb=1
    )
    database.add(checkout)
    database.flush()
    database.add(
        CheckoutItem(
            checkout_id=checkout.id,
            product_id=product.id,
            lot_id=lot.id,
            quantity=quantity,
            status_at_checkout="Approved",
        )
    )
    database.commit()


def _other_client_id(database, login):
    return database.query(Client).filter(Client.user_id != login.user.id).first().user_id


def _list_item(database, login, product, ticked=False):
    database.add(
        ShoppingListItem(
            client_id=login.user.id, product_id=product.id, text=product.name, ticked=ticked
        )
    )
    database.commit()


def test_list_item_is_recommended_with_the_list_reason_and_unrelated_products_are_not(
    database, logged_in_client
):
    login = logged_in_client(Role.CLIENT)
    beans, oats = _good_matches(database, login, 12)[-2:]
    _list_item(database, login, beans)
    _list_item(database, login, oats, ticked=True)  # ticked items don't count

    picks = _recommend(database, login)

    assert picks[0]["product_id"] == beans.id
    assert "It's on your shopping list." in picks[0]["rationale"]
    assert not any("shopping list" in pick["rationale"] for pick in picks[1:])


def test_a_product_in_the_active_cart_is_hidden(database, logged_in_client):
    login = logged_in_client(Role.CLIENT)
    beans, oats = _good_matches(database, login, 12)[-2:]
    _list_item(database, login, beans)
    _list_item(database, login, oats)
    session =ShoppingSession(Shopping_Session_Token="synthetic-cart", client_id=login.user.id)
    database.add(session)
    database.flush()
    cart = Cart(session_id=session.id)
    database.add(cart)
    database.flush()
    database.add(CartItem(cart_id=cart.id, product_id=beans.id, quantity=1))
    database.commit()

    ids = [p["product_id"] for p in _recommend(database, login)]
    assert ids[0] == oats.id and beans.id not in ids


def test_a_client_with_no_history_gets_the_most_taken_product_first(database, logged_in_client):
    login = logged_in_client(Role.CLIENT)
    other = _other_client_id(database, login)
    beans, oats = _good_matches(database, login, 12)[-2:]
    _checkout(database, other, oats, 2)
    _checkout(database, other, beans, 3)
    _checkout(database, other, beans, 2)

    picks = _recommend(database, login)

    assert picks[0]["product_id"] == beans.id  # 5 taken beats 2
    assert "Popular at the warehouse." in picks[0]["rationale"]
    assert picks[1]["product_id"] == oats.id
    assert "Popular at the warehouse." not in picks[2]["rationale"]  # never taken


def test_fallback_is_capped(database, logged_in_client):
    login = logged_in_client(Role.CLIENT)
    other = _other_client_id(database, login)
    products = database.query(Product).filter(Product.sku.like("SYN-PROD-%")).limit(POPULAR_COUNT + 2).all()
    for product in products:
        _checkout(database, other, product, 1)

    assert len(_recommend(database, login)) == POPULAR_COUNT == 12


def test_every_recommendation_is_a_clean_good_match(database, logged_in_client):
    picks = _recommend(database, logged_in_client(Role.CLIENT))
    assert picks
    assert all(p["status"] == "Approved" and not p["not_for"] and not p["allergy_match"] for p in picks)


def test_with_no_checkouts_at_all_the_first_twelve_good_match_products_are_shown(
    database, logged_in_client
):
    login = logged_in_client(Role.CLIENT)
    picks = _recommend(database, login)

    assert len(picks) == POPULAR_COUNT
    assert all(pick["status"] != "Restricted" for pick in picks)
    assert all("Popular" not in pick["rationale"] for pick in picks)
    first_lots = (
        database.query(InventoryLot)
        .filter(InventoryLot.quantity > 0)
        .order_by(InventoryLot.expiration_date, InventoryLot.id)
        .all()
    )
    assert picks[0]["product_id"] == first_lots[0].product_id  # oldest stock first


def test_an_item_one_household_member_is_allergic_to_is_never_suggested(database, logged_in_client):
    login = logged_in_client(Role.CLIENT)  # "Little one" has a nut allergy
    crackers = _product(database, "SYN-CRACK-001")
    database.add(ShoppingListItem(client_id=login.user.id, product_id=crackers.id, text="crackers"))
    database.commit()

    picks = _recommend(database, login)

    assert picks  # the other household picks still show
    assert crackers.id not in [pick["product_id"] for pick in picks]
