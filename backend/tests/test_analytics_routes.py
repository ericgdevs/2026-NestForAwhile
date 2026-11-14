from fastapi.testclient import TestClient

from app.auth import Role
from app.db import get_db
from app.main import app


def test_manager_analytics_is_aggregate_only(database, logged_in_client):
    app.dependency_overrides[get_db] = lambda: database
    try:
        response = TestClient(app).get(
            "/analytics", cookies=logged_in_client(Role.WAREHOUSE_MANAGER).cookies
        )
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 200
    payload = response.json()
    assert "families_served" in payload
    assert "client" not in response.text.lower()
    assert "email" not in response.text.lower()
    assert "id" not in payload
