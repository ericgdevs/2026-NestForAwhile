from fastapi.testclient import TestClient

from app.auth import Role
from app.db import get_db
from app.main import app


def test_scan_returns_local_product_and_friendly_unknown_404(database, logged_in_client):
    app.dependency_overrides[get_db] = lambda: database
    try:
        client = TestClient(app)
        response = client.get(
            "/products/scan/000000000001",
            cookies=logged_in_client(Role.CLIENT).cookies,
        )
        missing = client.get(
            "/products/scan/does-not-exist",
            cookies=logged_in_client(Role.CLIENT).cookies,
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["name"] == "Synthetic Rolled Oats"
    assert response.json()["status"] == "Approved"
    assert missing.status_code == 404
    assert "couldn't find" in missing.json()["detail"]


def _get(database, logged_in_client, role, path):
    app.dependency_overrides[get_db] = lambda: database
    try:
        return TestClient(app).get(path, cookies=logged_in_client(role).cookies)
    finally:
        app.dependency_overrides.clear()


def test_lookup_resolves_by_sku_and_by_barcode(database, logged_in_client):
    by_sku = _get(database, logged_in_client, Role.CLIENT, "/products/scan/SYN-OATS-001")
    by_barcode = _get(database, logged_in_client, Role.CLIENT, "/products/scan/000000000001")

    assert by_sku.status_code == by_barcode.status_code == 200
    assert by_sku.json()["product_id"] == by_barcode.json()["product_id"]


def test_labels_list_every_product_for_managers_only(database, logged_in_client):
    manager = _get(database, logged_in_client, Role.WAREHOUSE_MANAGER, "/products/labels")
    client = _get(database, logged_in_client, Role.CLIENT, "/products/labels")

    assert manager.status_code == 200
    assert {"sku": "SYN-OATS-001", "name": "Synthetic Rolled Oats"} in manager.json()
    assert client.status_code == 403
