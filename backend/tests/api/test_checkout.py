from datetime import UTC, datetime

import pytest
from sqlmodel import Session, select

from app.models import (Checkout, CheckoutItem, Intervention, InventoryLot, InventoryMovement, Role, SessionStatus,
                        ShoppingSession, Visit)
from app.services import checkout as checkout_service
from tests.unit.test_checkout_validation import add_product, start_with_cart


def _stock(session, product):
    return sorted(lot.quantity for lot in session.exec(select(InventoryLot).where(InventoryLot.product_id == product.id)))


def _validate(api, shopping):
    return api.post(f"/checkout/{shopping.Shopping_Session_Token}/validate")


def test_clean_checkout_decrements_fifo_and_writes_records(login_as, seeded):
    rice = add_product(seeded, "Rice", 2, weight_lb=1.5)
    seeded.add(InventoryLot(product_id=rice.id, quantity=5, received_at=datetime(2026, 2, 1, tzinfo=UTC)))
    seeded.commit()
    shopping = start_with_cart(seeded, [(rice, 4)])
    body = _validate(login_as(Role.VOLUNTEER), shopping).json()
    assert body["status"] == "completed" and body["receipt_id"]
    assert _stock(seeded, rice) == [0, 3]  # oldest lot emptied first, then 2 from the next
    assert sorted(m.change for m in seeded.exec(select(InventoryMovement))) == [-2, -2]
    assert seeded.exec(select(CheckoutItem)).one().quantity == 4
    assert seeded.exec(select(Visit)).one().pounds_distributed == 6.0
    assert seeded.get(ShoppingSession, shopping.id).status == SessionStatus.COMPLETED


def test_restricted_item_hard_stops_then_passes_after_intervention(login_as, seeded):
    rice = add_product(seeded, "Rice", 5)
    nuts = add_product(seeded, "Peanut Butter", 5, allergens=["peanuts"])
    shopping = start_with_cart(seeded, [(rice, 1), (nuts, 1)])
    api = login_as(Role.VOLUNTEER)
    blocked = _validate(api, shopping).json()
    assert blocked["status"] == "blocked" and [i["status"] for i in blocked["blocked_items"]] == ["Restricted"]
    assert _stock(seeded, nuts) == [5] and not seeded.exec(select(InventoryMovement)).all()

    url = f"/checkout/{shopping.Shopping_Session_Token}/interventions"
    assert api.post(url, json={"product_id": nuts.id, "action": "removed_item", "note": "client agreed"}).status_code == 200
    assert seeded.exec(select(Intervention)).one().product_id == nuts.id
    assert _validate(api, shopping).json()["status"] == "completed"
    assert seeded.exec(select(Checkout)).one().status == "completed"
    assert _stock(seeded, nuts) == [5] and _stock(seeded, rice) == [4]


def test_shortfall_blocks(login_as, seeded):
    rice = add_product(seeded, "Rice", 1)
    shopping = start_with_cart(seeded, [(rice, 2)])
    assert _validate(login_as(Role.MANAGER), shopping).json()["status"] == "blocked"
    assert _stock(seeded, rice) == [1]


def test_failure_mid_checkout_rolls_everything_back(seeded, monkeypatch):
    rice, beans = add_product(seeded, "Rice", 5), add_product(seeded, "Beans", 5)
    shopping = start_with_cart(seeded, [(beans, 1), (rice, 2)])
    real, calls = checkout_service.movements.log_movement, []

    def flaky(*args, **kwargs):
        calls.append(1)
        if len(calls) == 2:
            raise RuntimeError("disk full")
        return real(*args, **kwargs)

    monkeypatch.setattr(checkout_service.movements, "log_movement", flaky)
    with pytest.raises(RuntimeError):
        checkout_service.complete_checkout(seeded, shopping.Shopping_Session_Token, user_id=1)
    assert _stock(seeded, rice) == [5] and _stock(seeded, beans) == [5]
    for model in (InventoryMovement, CheckoutItem, Visit):
        assert not seeded.exec(select(model)).all()
    assert seeded.get(ShoppingSession, shopping.id).status == SessionStatus.ACTIVE
    assert not seeded.exec(select(Checkout)).all()


def test_stale_stock_read_cannot_oversell_last_unit(seeded, monkeypatch):
    rice = add_product(seeded, "Rice", 1)
    first = start_with_cart(seeded, [(rice, 1)])
    # Another checkout takes the last unit after this one validated
    monkeypatch.setattr(checkout_service, "find_blocked_items", lambda *a, **k: [])
    lot = seeded.exec(select(InventoryLot).where(InventoryLot.product_id == rice.id)).one()
    stale_lots = [lot]
    monkeypatch.setattr(checkout_service.fifo, "usable_lots_fifo", lambda *a, **k: stale_lots)
    seeded.connection().exec_driver_sql("UPDATE inventory_lots SET quantity = 0 WHERE id = ?", (lot.id,))
    seeded.commit()
    result = checkout_service.complete_checkout(seeded, first.Shopping_Session_Token, user_id=1)
    assert result.status == "blocked" and result.blocked_items[0].product_id == rice.id
    assert _stock(seeded, rice) == [0] and not seeded.exec(select(InventoryMovement)).all()


def test_session_claim_prevents_duplicate_checkout_with_stale_session_reads(seeded):
    rice = add_product(seeded, "Rice", 2)
    shopping = start_with_cart(seeded, [(rice, 1)])
    first = Session(seeded.get_bind())
    second = Session(seeded.get_bind())
    try:
        first_shopping = first.get(ShoppingSession, shopping.id)
        second_shopping = second.get(ShoppingSession, shopping.id)
        assert first_shopping.status == second_shopping.status == SessionStatus.ACTIVE

        assert checkout_service._claim_session_for_checkout(first, first_shopping)
        first.commit()
        assert not checkout_service._claim_session_for_checkout(second, second_shopping)
        second.rollback()
    finally:
        first.close()
        second.close()


def test_queue_promotion_failure_rolls_back_checkout(seeded, monkeypatch):
    rice = add_product(seeded, "Rice", 5)
    shopping = start_with_cart(seeded, [(rice, 1)])

    def fail_promotion(_):
        raise RuntimeError("queue unavailable")

    monkeypatch.setattr(checkout_service, "_refresh_queue", fail_promotion)
    with pytest.raises(RuntimeError, match="queue unavailable"):
        checkout_service.complete_checkout(seeded, shopping.Shopping_Session_Token, user_id=1)

    assert _stock(seeded, rice) == [5]
    assert seeded.get(ShoppingSession, shopping.id).status == SessionStatus.ACTIVE
    for model in (Checkout, CheckoutItem, InventoryMovement, Visit):
        assert not seeded.exec(select(model)).all()


def test_checkout_roles_and_unknown_token(login_as, seeded):
    assert login_as(Role.CLIENT).post("/checkout/x/validate").status_code == 403
    assert login_as(Role.VOLUNTEER).post("/checkout/nope/validate").status_code == 404
