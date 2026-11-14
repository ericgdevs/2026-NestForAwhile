from datetime import UTC, date, datetime, timedelta

from app.models import InventoryLocation, InventoryLot, Product, Role
from app.services import replenishment

TODAY = date(2026, 11, 14)


def _stock(session, name, aisle, qty, threshold, expires=None):
    product = Product(sku=name, barcode=name, name=name, category="x")
    loc = InventoryLocation(aisle=aisle, shelf="S1", bin="B1")
    session.add_all([product, loc])
    session.flush()
    session.add(InventoryLot(product_id=product.id, location_id=loc.id, quantity=qty, reorder_threshold=threshold,
                             received_at=datetime(2026, 1, 1, tzinfo=UTC), expiration_date=expires))
    session.commit()


def _names(session, sort):
    return [i.name for i in replenishment.list_replenishment(session, sort, TODAY)]


def test_only_below_threshold_listed_by_ratio(session):
    _stock(session, "Beans", "A1", 5, 10)   # 0.5
    _stock(session, "Rice", "A2", 1, 10)    # 0.1
    _stock(session, "Corn", "A3", 10, 10)   # at threshold: not listed
    items = replenishment.list_replenishment(session, "priority", TODAY)
    assert [(i.name, i.priority) for i in items] == [("Rice", 1), ("Beans", 2)]


def test_location_sort_is_aisle_sequence(session):
    _stock(session, "Beans", "A10", 1, 10)
    _stock(session, "Rice", "A2", 5, 10)
    _stock(session, "Corn", "B1", 0, 10)
    assert _names(session, "location") == ["Rice", "Beans", "Corn"]
    assert _names(session, "name") == ["Beans", "Corn", "Rice"]


def test_expired_stock_does_not_count(session):
    _stock(session, "Milk", "A1", 20, 10, expires=TODAY - timedelta(days=1))
    assert _names(session, "priority") == ["Milk"]


def test_replenishment_route_roles_and_shape(login_as, seeded):
    body = login_as(Role.STAFF).get("/inventory/replenishment?sort=location").json()
    assert body and set(body[0]) == {"product_id", "name", "quantity", "reorder_threshold", "aisle", "shelf", "bin", "priority"}
    assert login_as(Role.STAFF).get("/inventory/replenishment?sort=bogus").status_code == 422
    assert login_as(Role.VOLUNTEER).get("/inventory/replenishment").status_code == 403
