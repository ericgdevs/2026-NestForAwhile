from fastapi.testclient import TestClient

from app.auth import Role
from app.db import get_db
from app.main import app
from app.models import CapacitySetting, Cart, CartItem, Client, Product, ShoppingSession, User
from app.services.checkout import complete_checkout


def _api(database):
    app.dependency_overrides[get_db] = lambda: database
    return TestClient(app)


def _active_client(database):
    return database.query(User).filter_by(role="Client").first()


def test_signing_in_twice_keeps_one_visit(database):
    try:
        api = _api(database)
        body = {"email": "client.active@example.test", "password": "demo-password"}
        first = api.post("/auth/login", json=body).json()
        second = api.post("/auth/login", json=body).json()
    finally:
        app.dependency_overrides.clear()
    user = _active_client(database)
    assert first["Shopping_Session_Token"] == second["Shopping_Session_Token"]
    assert (
        database.query(ShoppingSession).filter_by(client_id=user.id, status="active").count() == 1
    )


def test_check_in_starts_a_visit_once_and_reports_shopping(database, logged_in_client):
    cookies = logged_in_client(Role.CLIENT).cookies
    try:
        api = _api(database)
        before = api.get("/me/visit", cookies=cookies).json()
        started = api.post("/me/check-in", cookies=cookies).json()
        again = api.post("/me/check-in", cookies=cookies).json()
    finally:
        app.dependency_overrides.clear()
    assert before == {"status": "none"}
    assert started["status"] == "shopping"
    assert again["Shopping_Session_Token"] == started["Shopping_Session_Token"]


def test_pending_client_stays_awaiting_approval(database):
    pending = database.query(Client).filter_by(Client_Enrollment_Status="Pending").one()
    from app.auth import create_access_token

    cookies = {"session": create_access_token(pending.user_id, Role.CLIENT)}
    try:
        state = _api(database).post("/me/check-in", cookies=cookies).json()
    finally:
        app.dependency_overrides.clear()
    assert state == {"status": "awaiting_approval"}
    assert database.query(ShoppingSession).filter_by(client_id=pending.user_id).count() == 0


def test_full_floor_puts_the_client_in_the_queue(database, logged_in_client):
    setting = database.query(CapacitySetting).first()
    if setting is None:
        setting = CapacitySetting(Max_Floor_Capacity=0)
        database.add(setting)
    setting.Max_Floor_Capacity = 0
    database.commit()
    try:
        state = (
            _api(database)
            .post("/me/check-in", cookies=logged_in_client(Role.CLIENT).cookies)
            .json()
        )
    finally:
        app.dependency_overrides.clear()
    assert state["status"] == "queued" and state["position"] == 1


def test_after_checkout_the_phone_sees_visit_complete(database, logged_in_client):
    login = logged_in_client(Role.CLIENT)
    volunteer = database.query(User).filter_by(role="Volunteer").first()
    session = ShoppingSession(Shopping_Session_Token="synthetic-visit", client_id=login.user.id)
    database.add(session)
    database.flush()
    cart = Cart(session_id=session.id)
    database.add(cart)
    database.flush()
    oats = database.query(Product).filter_by(sku="SYN-OATS-001").one()
    database.add(CartItem(cart_id=cart.id, product_id=oats.id, quantity=1))
    database.commit()
    complete_checkout(database, session, volunteer)
    try:
        state = _api(database).get("/me/visit", cookies=login.cookies).json()
    finally:
        app.dependency_overrides.clear()
    assert state["status"] == "complete"
    assert state["receipt"]["checkout_id"] and state["receipt"]["total_lb"] > 0
