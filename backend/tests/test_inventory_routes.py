from datetime import date, timedelta

from fastapi.testclient import TestClient

from app.auth import Role
from app.db import get_db
from app.main import app
from app.models import InventoryLot, Product


def test_staff_can_audit_product_and_update_inventory(database, logged_in_client):
    auth = logged_in_client(Role.WAREHOUSE_STAFF)
    product = Product(
        sku="TEST-AUDIT",
        barcode="999000000001",
        name="Synthetic Audit Product",
        category="test",
    )
    database.add(product)
    database.flush()
    database.add(
        InventoryLot(
            product_id=product.id,
            quantity=4,
            expiration_date=date.today() + timedelta(days=30),
            aisle="A",
            shelf="1",
            bin="1",
            reorder_threshold=2,
        )
    )
    database.commit()
    app.dependency_overrides[get_db] = lambda: database
    try:
        response = TestClient(app).post(
            "/inventory/audit",
            json={"product_id": product.id, "counted_qty": 2},
            cookies=auth.cookies,
        )
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json()["variance"] == -2
    assert database.query(InventoryLot).filter_by(product_id=product.id).one().quantity == 2


def test_inventory_lots_and_replenishment_are_ordered(database, logged_in_client):
    auth = logged_in_client(Role.WAREHOUSE_STAFF)
    product = Product(
        sku="TEST-LOTS",
        barcode="999000000002",
        name="Synthetic Lots Product",
        category="test",
    )
    database.add(product)
    database.flush()
    database.add_all(
        [
            InventoryLot(
                product_id=product.id,
                quantity=1,
                expiration_date=date.today() + timedelta(days=7),
                aisle="B",
                shelf="2",
                bin="2",
                reorder_threshold=5,
            ),
            InventoryLot(
                product_id=product.id,
                quantity=2,
                expiration_date=date.today() + timedelta(days=8),
                aisle="A",
                shelf="1",
                bin="1",
                reorder_threshold=5,
            ),
        ]
    )
    database.commit()
    app.dependency_overrides[get_db] = lambda: database
    try:
        client = TestClient(app)
        lots = client.get("/inventory/lots", cookies=auth.cookies)
        replenishment = client.get("/inventory/replenishment?sort=priority", cookies=auth.cookies)
    finally:
        app.dependency_overrides.clear()
    product_lots = [row for row in lots.json() if row["product_id"] == product.id]
    assert [row["expiring_soon"] for row in product_lots] == [True, False]
    assert replenishment.status_code == 200
    assert replenishment.json()[0]["priority"] <= replenishment.json()[1]["priority"]
