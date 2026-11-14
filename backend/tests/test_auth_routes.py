from fastapi.testclient import TestClient

from app.auth import Role
from app.db import get_db
from app.main import app


def test_active_client_login_creates_session(database):
    app.dependency_overrides[get_db] = lambda: database
    try:
        response = TestClient(app).post(
            "/auth/login",
            json={"email": "client.active@example.test", "password": "demo-password"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["Shopping_Session_Token"]
    assert response.cookies.get("session")


def test_invalid_and_non_active_login_are_rejected(database):
    app.dependency_overrides[get_db] = lambda: database
    try:
        client = TestClient(app)
        assert client.post(
            "/auth/login",
            json={"email": "client.active@example.test", "password": "wrong"},
        ).status_code == 401
        assert client.post(
            "/auth/login",
            json={"email": "client.inactive@example.test", "password": "demo-password"},
        ).status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_capacity_is_visible_to_volunteer(database, logged_in_client):
    app.dependency_overrides[get_db] = lambda: database
    try:
        response = TestClient(app).get(
            "/capacity", cookies=logged_in_client(Role.VOLUNTEER).cookies
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "Active_Floor_Shoppers": 0,
        "Max_Floor_Capacity": 10,
        "Queue_Waiting": 0,
    }
