from fastapi.testclient import TestClient

from app.auth import Role, email_lookup_hash, hash_password
from app.db import get_db
from app.main import app
from app.models import (
    CapacitySetting,
    Cart,
    CartItem,
    Checkout,
    Client,
    InventoryLot,
    Product,
    QueueEntry,
    ShoppingSession,
    User,
    Visit,
)
from app.services import checkout as checkout_service
from app.services import queue


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


def _full_floor_with_waiting_client(database, logged_in_client):
    client_user = logged_in_client(Role.CLIENT).user
    volunteer = logged_in_client(Role.VOLUNTEER).user
    setting = database.query(CapacitySetting).first() or CapacitySetting()
    setting.Max_Floor_Capacity = 1
    database.add(setting)
    session = ShoppingSession(
        Shopping_Session_Token="synthetic-atomic-session", client_id=client_user.id
    )
    waiting_user = User(
        email="client.waiting@example.test",
        email_hash=email_lookup_hash("client.waiting@example.test"),
        password_hash=hash_password("demo-password"),
        role=Role.CLIENT.value,
    )
    database.add_all([session, waiting_user])
    database.flush()
    database.add(
        Client(
            user_id=waiting_user.id,
            name="Synthetic Waiting Client",
            Household_Size=1,
            Client_Enrollment_Status="Active",
        )
    )
    cart = Cart(session_id=session.id)
    database.add(cart)
    database.flush()
    product = database.query(Product).filter_by(sku="SYN-OATS-001").one()
    database.add(CartItem(cart_id=cart.id, product_id=product.id, quantity=1))
    entry = QueueEntry(client_id=waiting_user.id, status="waiting")
    database.add(entry)
    database.commit()
    return session, volunteer, entry, product


def test_checkout_releases_slot_and_promotes_next_waiting_client(database, logged_in_client):
    session, volunteer, entry, _ = _full_floor_with_waiting_client(database, logged_in_client)
    assert queue.active_count(database) == 1

    checkout_service.complete_checkout(database, session, volunteer)

    assert database.get(QueueEntry, entry.id).status == "ready"
    assert queue.active_count(database) == 1  # slot released, then taken by the promoted client
    assert database.query(ShoppingSession).filter_by(status="active").count() == 0


def test_promotion_failure_rolls_back_whole_checkout(database, logged_in_client, monkeypatch):
    session, volunteer, entry, product = _full_floor_with_waiting_client(database, logged_in_client)
    stock_before = [
        lot.quantity for lot in database.query(InventoryLot).filter_by(product_id=product.id)
    ]

    def fail(_database):
        raise RuntimeError("promotion failed")

    monkeypatch.setattr(queue, "promote_waiting", fail)
    try:
        checkout_service.complete_checkout(database, session, volunteer)
    except RuntimeError:
        pass
    else:
        raise AssertionError("expected promotion failure to propagate")

    assert database.query(Checkout).count() == 0
    assert database.query(Visit).count() == 0
    assert database.get(ShoppingSession, session.id).status == "active"
    assert database.get(QueueEntry, entry.id).status == "waiting"
    stock_after = [
        lot.quantity for lot in database.query(InventoryLot).filter_by(product_id=product.id)
    ]
    assert stock_after == stock_before
