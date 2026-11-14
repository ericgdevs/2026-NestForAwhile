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
