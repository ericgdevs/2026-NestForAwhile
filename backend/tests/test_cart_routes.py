from fastapi.testclient import TestClient

from app.auth import Role
from app.db import get_db
from app.main import app
from app.models import Product, ShoppingSession


def test_cart_persists_items_in_active_session(database, logged_in_client):
    user = logged_in_client(Role.CLIENT).user
    database.add(
        ShoppingSession(
            Shopping_Session_Token="synthetic-cart-session",
            client_id=user.id,
        )
    )
    database.commit()
    product = database.query(Product).filter_by(sku="SYN-OATS-001").one()
    app.dependency_overrides[get_db] = lambda: database
    try:
        client = TestClient(app)
        cookies = logged_in_client(Role.CLIENT).cookies
        added = client.post(
            "/cart/items",
            json={"product_id": product.id, "quantity": 3},
            cookies=cookies,
        )
        current = client.get("/cart", cookies=cookies)
    finally:
        app.dependency_overrides.clear()

    assert added.status_code == 200
    assert current.json()["items"][0]["quantity"] == 3


def test_cart_items_carry_nutrition_and_rules_status(database, logged_in_client):
    user = logged_in_client(Role.CLIENT).user
    database.add(
        ShoppingSession(
            Shopping_Session_Token="synthetic-cart-label-session",
            client_id=user.id,
        )
    )
    database.commit()
    product = database.query(Product).filter_by(sku="SYN-OATS-001").one()
    app.dependency_overrides[get_db] = lambda: database
    try:
        client = TestClient(app)
        cookies = logged_in_client(Role.CLIENT).cookies
        client.post("/cart/items", json={"product_id": product.id, "quantity": 1}, cookies=cookies)
        item = client.get("/cart", cookies=cookies).json()["items"][0]
    finally:
        app.dependency_overrides.clear()

    assert item["sku"] == "SYN-OATS-001"
    assert item["sodium_mg"] == product.sodium_mg
    assert item["calories"] == product.calories and item["fiber_g"] == product.fiber_g
    assert item["total_fat_g"] is None  # not in the catalog: left empty, never made up
    assert item["status"] in {"Approved", "Capped", "Restricted"}
    assert item["explanation"]


def test_a_parallel_request_creating_the_cart_first_does_not_fail(database, logged_in_client):
    from app.services.cart import get_or_create_cart

    user = logged_in_client(Role.CLIENT).user
    session = ShoppingSession(Shopping_Session_Token="synthetic-cart-race", client_id=user.id)
    database.add(session)
    database.commit()
    existing = get_or_create_cart(database, session)
    database.commit()

    real_scalar, calls = database.scalar, []

    def stale_first_lookup(*args, **kwargs):
        calls.append(1)  # the first lookup misses, as when another request has not committed yet
        return None if len(calls) == 1 else real_scalar(*args, **kwargs)

    database.scalar = stale_first_lookup
    try:
        assert get_or_create_cart(database, session).id == existing.id
    finally:
        del database.scalar
