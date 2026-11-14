from fastapi.testclient import TestClient

from app.auth import Role
from app.db import get_db
from app.main import app


def test_capacity_allows_staff_roles_and_rejects_clients(database, logged_in_client):
    app.dependency_overrides[get_db] = lambda: database
    try:
        client = TestClient(app)
        assert (
            client.get("/capacity", cookies=logged_in_client(Role.VOLUNTEER).cookies).status_code
            == 200
        )
        assert (
            client.get(
                "/capacity",
                cookies=logged_in_client(Role.WAREHOUSE_STAFF).cookies,
            ).status_code
            == 200
        )
        assert (
            client.get("/capacity", cookies=logged_in_client(Role.CLIENT).cookies).status_code
            == 403
        )
        assert client.get("/capacity").status_code == 401
    finally:
        app.dependency_overrides.clear()
