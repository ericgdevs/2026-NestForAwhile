from datetime import UTC, date, datetime, timedelta

import pytest

from app.models import InventoryLot, Product, Role
from app.services import fifo

TODAY = date(2026, 11, 14)


def _lot(session, product_id, received, expires=None, qty=5):
    lot = InventoryLot(product_id=product_id, quantity=qty, received_at=received, expiration_date=expires)
    session.add(lot)
    session.commit()
    return lot


@pytest.fixture
def product(session):
    p = Product(sku="S1", barcode="B1", name="Synthetic Beans", category="Canned")
    session.add(p)
    session.commit()
    return p


@pytest.mark.parametrize("days,flagged", [(-1, False), (0, True), (7, True), (8, False)])
def test_expiring_soon_boundary(session, product, days, flagged):
    lot = _lot(session, product.id, datetime(2026, 1, 1, tzinfo=UTC), TODAY + timedelta(days=days))
    assert fifo.is_expiring_soon(lot, TODAY) is flagged


def test_fifo_order_expiry_then_arrival_then_id(session, product):
    day = datetime(2026, 1, 2, tzinfo=UTC)
    newer = _lot(session, product.id, datetime(2026, 1, 3, tzinfo=UTC), TODAY + timedelta(days=1))
    later_expiry = _lot(session, product.id, day, TODAY + timedelta(days=30))
    sooner_expiry = _lot(session, product.id, day, TODAY + timedelta(days=10))
    oldest = _lot(session, product.id, datetime(2026, 1, 1, tzinfo=UTC), None)
    order = [lot.id for lot in fifo.all_lots_fifo(session)]
    assert order == [newer.id, sooner_expiry.id, later_expiry.id, oldest.id]


def test_usable_lots_skip_expired_and_empty(session, product):
    _lot(session, product.id, datetime(2026, 1, 1, tzinfo=UTC), TODAY - timedelta(days=1))
    _lot(session, product.id, datetime(2026, 1, 2, tzinfo=UTC), TODAY + timedelta(days=3), qty=0)
    good = _lot(session, product.id, datetime(2026, 1, 3, tzinfo=UTC), TODAY)
    assert [lot.id for lot in fifo.usable_lots_fifo(session, product.id, TODAY)] == [good.id]


def test_lots_route_matches_contract_and_roles(login_as, seeded):
    body = login_as(Role.STAFF).get("/inventory/lots").json()
    assert body and set(body[0]) == {"lot_id", "product_id", "quantity", "expiration_date", "expiring_soon"}
    assert login_as(Role.CLIENT).get("/inventory/lots").status_code == 403
