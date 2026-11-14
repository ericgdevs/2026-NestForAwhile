from fastapi.testclient import TestClient

from app.auth import Role
from app.db import get_db
from app.main import app
from app.models import Client


def _call(database, method, path, cookies):
    app.dependency_overrides[get_db] = lambda: database
    try:
        return TestClient(app).request(method, path, cookies=cookies)
    finally:
        app.dependency_overrides.clear()


def test_only_managers_see_pending_clients_with_names(database, logged_in_client):
    manager = _call(
        database, "GET", "/clients/pending", logged_in_client(Role.WAREHOUSE_MANAGER).cookies
    )
    for role in (Role.CLIENT, Role.VOLUNTEER, Role.WAREHOUSE_STAFF, Role.DIRECTOR):
        assert (
            _call(database, "GET", "/clients/pending", logged_in_client(role).cookies).status_code
            == 403
        )

    assert manager.status_code == 200
    assert [row["name"] for row in manager.json()] == ["Pending Client"]


def test_manager_approval_activates_and_records_who(database, logged_in_client):
    manager = logged_in_client(Role.WAREHOUSE_MANAGER)
    pending = database.query(Client).filter_by(Client_Enrollment_Status="Pending").one()

    volunteer_try = _call(
        database,
        "POST",
        f"/clients/{pending.user_id}/approve",
        logged_in_client(Role.VOLUNTEER).cookies,
    )
    approved = _call(database, "POST", f"/clients/{pending.user_id}/approve", manager.cookies)
    again = _call(database, "POST", f"/clients/{pending.user_id}/approve", manager.cookies)

    database.refresh(pending)
    assert volunteer_try.status_code == 403
    assert approved.json()["Client_Enrollment_Status"] == "Active"
    assert pending.approved_by == manager.user.id and pending.approved_at is not None
    assert again.status_code == 404


def test_pending_client_cannot_complete_checkout_until_approved(database):
    from app.models import Cart, CartItem, Product, ShoppingSession
    from app.services.checkout import validate_checkout

    pending = database.query(Client).filter_by(Client_Enrollment_Status="Pending").one()
    session = ShoppingSession(Shopping_Session_Token="synthetic-pending", client_id=pending.user_id)
    database.add(session)
    database.flush()
    cart = Cart(session_id=session.id)
    database.add(cart)
    database.flush()
    oats = database.query(Product).filter_by(sku="SYN-OATS-001").one()
    database.add(CartItem(cart_id=cart.id, product_id=oats.id, quantity=1))
    database.commit()

    assert "This account is waiting for staff approval." in validate_checkout(database, session)
    pending.Client_Enrollment_Status = "Active"
    database.commit()
    assert "This account is waiting for staff approval." not in validate_checkout(database, session)
