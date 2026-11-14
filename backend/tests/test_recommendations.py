from fastapi.testclient import TestClient

from app.auth import Role
from app.db import get_db
from app.main import app


def test_recommendations_scale_to_household_and_exclude_restricted(database, logged_in_client):
    app.dependency_overrides[get_db] = lambda: database
    try:
        response = TestClient(app).get(
            "/recommendations",
            cookies=logged_in_client(Role.CLIENT).cookies,
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    items = response.json()
    assert items
    assert all(item["status"] != "Restricted" for item in items)
    assert all(item["quantity"] == 2 for item in items)
    assert all(item["rationale"] for item in items)
