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
