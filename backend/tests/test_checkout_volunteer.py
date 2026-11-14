import json

import pytest
from fastapi.testclient import TestClient

from app.auth import Role
from app.db import get_db
from app.main import app
from app.models import Cart, CartItem, Client, Intervention, InventoryLot, Product, ShoppingSession

TOKEN = "synthetic-volunteer-checkout"


@pytest.fixture
def cart_with(database, logged_in_client):
    """Active client (Person 1 + Little one with a nut allergy) with given SKUs in the cart."""

    def build(*skus):
        user = logged_in_client(Role.CLIENT).user
        session = ShoppingSession(Shopping_Session_Token=TOKEN, client_id=user.id)
        database.add(session)
        database.flush()
        cart = Cart(session_id=session.id)
        database.add(cart)
        database.flush()
        for sku in skus:
            product = database.query(Product).filter_by(sku=sku).one()
            database.add(CartItem(cart_id=cart.id, product_id=product.id, quantity=1))
        database.commit()
        return user

    return build


def _call(database, method, path, role_cookies, **kwargs):
    app.dependency_overrides[get_db] = lambda: database
    try:
        return TestClient(app).request(method, path, cookies=role_cookies, **kwargs)
    finally:
        app.dependency_overrides.clear()


def _stock(database, sku):
    product = database.query(Product).filter_by(sku=sku).one()
    return sum(
        lot.quantity for lot in database.query(InventoryLot).filter_by(product_id=product.id)
    )


def test_allergy_item_pauses_checkout_until_acknowledged(database, logged_in_client, cart_with):
    cart_with("SYN-CRACK-001")
    volunteer = logged_in_client(Role.VOLUNTEER).cookies
    crackers = database.query(Product).filter_by(sku="SYN-CRACK-001").one()
    before = _stock(database, "SYN-CRACK-001")

    review = _call(database, "GET", f"/checkout/lookup?token={TOKEN}", volunteer).json()
    blocked = _call(database, "POST", f"/checkout/{TOKEN}/complete", volunteer)
    ack = _call(
        database,
        "POST",
        f"/checkout/{TOKEN}/acknowledge",
        volunteer,
        json={"product_id": crackers.id},
    )
    done = _call(database, "POST", f"/checkout/{TOKEN}/complete", volunteer)

    assert review["items"][0]["status"] == "Capped" and review["blocking"] == []
    assert review["needs_ack"][0]["not_for"] == [
        {"nickname": "Little one", "reason": "Nut Allergy"}
    ]
    assert blocked.status_code == 409 and "Confirm with the client" in blocked.json()["detail"]
    assert ack.json()["needs_ack"] == [] and ack.json()["items"][0]["acknowledged"] is True
    assert done.status_code == 200
    assert _stock(database, "SYN-CRACK-001") == before - 1
    assert database.query(Intervention).filter_by(action="allergy_ack").count() == 1


def test_red_item_blocks_until_removed_or_manager_override(database, logged_in_client, cart_with):
    user = cart_with("SYN-CRACK-001")
    for member in database.get(Client, user.id).members:
        member.allergies = json.dumps(["Nut Allergy"])
    database.commit()
    crackers = database.query(Product).filter_by(sku="SYN-CRACK-001").one()
    volunteer = logged_in_client(Role.VOLUNTEER).cookies
    manager = logged_in_client(Role.WAREHOUSE_MANAGER).cookies

    review = _call(database, "GET", f"/checkout/lookup?client_id={user.id}", volunteer).json()
    volunteer_override = _call(
        database,
        "POST",
        f"/checkout/{TOKEN}/override",
        volunteer,
        json={"product_id": crackers.id, "note": "x"},
    )
    no_reason = _call(
        database, "POST", f"/checkout/{TOKEN}/override", manager, json={"product_id": crackers.id}
    )
    overridden = _call(
        database,
        "POST",
        f"/checkout/{TOKEN}/override",
        manager,
        json={
            "product_id": crackers.id,
            "note": "Synthetic demo: client confirmed it is for a guest.",
        },
    ).json()

    assert review["items"][0]["status"] == "Restricted"
    assert any("isn't safe for anyone" in stop for stop in review["blocking"])
    assert volunteer_override.status_code == 403 and no_reason.status_code == 422
    assert overridden["blocking"] == [] and overridden["items"][0]["overridden"] is True


def test_volunteer_adds_forgotten_item_and_removes_one_both_logged(
    database, logged_in_client, cart_with
):
    cart_with("SYN-OATS-001")
    volunteer = logged_in_client(Role.VOLUNTEER).cookies
    oats = database.query(Product).filter_by(sku="SYN-OATS-001").one()

    added = _call(
        database, "POST", f"/checkout/{TOKEN}/items", volunteer, json={"code": "000000000002"}
    ).json()
    removed = _call(database, "DELETE", f"/checkout/{TOKEN}/items/{oats.id}", volunteer).json()
    unknown = _call(database, "POST", f"/checkout/{TOKEN}/items", volunteer, json={"code": "nope"})
    client_try = _call(
        database, "GET", f"/checkout/lookup?token={TOKEN}", logged_in_client(Role.CLIENT).cookies
    )

    assert {i["name"] for i in added["items"]} == {"Synthetic Rolled Oats", "Synthetic Black Beans"}
    assert [i["name"] for i in removed["items"]] == ["Synthetic Black Beans"]
    assert {e.action for e in database.query(Intervention)} == {"volunteer_added", "removed_item"}
    assert unknown.status_code == 404 and client_try.status_code == 403


def test_lookup_needs_a_token_or_client_id(database, logged_in_client):
    volunteer = logged_in_client(Role.VOLUNTEER).cookies
    assert _call(database, "GET", "/checkout/lookup", volunteer).status_code == 422
    assert _call(database, "GET", "/checkout/lookup?token=missing", volunteer).status_code == 404
