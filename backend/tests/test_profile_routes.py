from fastapi.testclient import TestClient
from sqlalchemy import text

from app.auth import Role
from app.db import get_db
from app.main import app
from app.models import Client, DietaryProfile


def test_client_profile_is_saved_and_tier_recomputed(database, logged_in_client):
    app.dependency_overrides[get_db] = lambda: database
    try:
        response = TestClient(app).put(
            "/me/profile",
            json={
                "restrictions": ["Low Sodium", "Vegetarian"],
                "allergies": ["contains_tree_nut"],
                "preferences": ["Budget friendly"],
            },
            cookies=logged_in_client(Role.CLIENT).cookies,
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["Dietary_Tier_ID"] == 6
    client = database.get(Client, logged_in_client(Role.CLIENT).user.id)
    profile = database.get(DietaryProfile, client.user_id)
    assert profile.restrictions == '["Low Sodium", "Vegetarian"]'
    raw = database.execute(
        text("SELECT restrictions FROM dietary_profiles WHERE client_id = :client_id"),
        {"client_id": client.user_id},
    ).scalar_one()
    assert raw != '["Low Sodium", "Vegetarian"]'
    assert client.Dietary_Tier_ID == 6


def test_profile_rejects_unknown_restriction(database, logged_in_client):
    app.dependency_overrides[get_db] = lambda: database
    try:
        response = TestClient(app).put(
            "/me/profile",
            json={"restrictions": ["Not A Real Restriction"]},
            cookies=logged_in_client(Role.CLIENT).cookies,
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
