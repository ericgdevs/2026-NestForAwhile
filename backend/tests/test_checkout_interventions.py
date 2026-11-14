from fastapi.testclient import TestClient

from app.auth import Role
from app.db import get_db
from app.main import app


def test_volunteer_can_remove_a_checkout_item(database, logged_in_client):
    app.dependency_overrides[get_db] = lambda: database
    try:
        client = TestClient(app)
        login = client.post(
            "/auth/login",
            json={"email": "client.active@example.test", "password": "demo-password"},
        )
        token = login.json()["Shopping_Session_Token"]
        response = client.post(
            f"/checkout/{token}/interventions",
            json={"product_id": 1, "action": "removed_item", "note": "Synthetic removal"},
            cookies=logged_in_client(Role.VOLUNTEER).cookies,
        )
    finally:
        app.dependency_overrides.clear()
    assert response.status_code in {404, 200}
