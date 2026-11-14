from fastapi.testclient import TestClient

from app.auth import Role
from app.db import get_db
from app.main import app
from app.models import Cart, CartItem, Product, ShoppingSession


def test_checkout_validation_and_completion_decrement_inventory(database, logged_in_client):
    client_user = logged_in_client(Role.CLIENT).user
    volunteer = logged_in_client(Role.VOLUNTEER)
    session = ShoppingSession(
        Shopping_Session_Token="synthetic-checkout-session",
        client_id=client_user.id,
    )
    database.add(session)
    database.flush()
    cart = Cart(session_id=session.id)
    database.add(cart)
    database.flush()
    product = database.query(Product).filter_by(sku="SYN-OATS-001").one()
    database.add(CartItem(cart_id=cart.id, product_id=product.id, quantity=1))
    database.commit()
    app.dependency_overrides[get_db] = lambda: database
    try:
        response = TestClient(app).post(
            f"/checkout/{session.Shopping_Session_Token}/complete",
            cookies=volunteer.cookies,
        )
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 200
    assert database.get(ShoppingSession, session.id).status == "completed"
