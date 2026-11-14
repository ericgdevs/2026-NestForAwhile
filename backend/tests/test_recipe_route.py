from fastapi.testclient import TestClient

from app.auth import Role
from app.db import get_db
from app.main import app
from app.models import ShoppingSession


def test_recipe_route_falls_back_when_provider_is_unavailable(database, logged_in_client):
    user = logged_in_client(Role.CLIENT).user
    database.add(
        ShoppingSession(
            Shopping_Session_Token="synthetic-recipe-session",
            client_id=user.id,
        )
    )
    database.commit()
    app.dependency_overrides[get_db] = lambda: database
    try:
        response = TestClient(app).post(
            "/recipes",
            cookies=logged_in_client(Role.CLIENT).cookies,
        )
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json()["used_fallback"] is True
