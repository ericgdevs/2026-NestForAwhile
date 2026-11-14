import json

from fastapi.testclient import TestClient
from sqlalchemy import text

from app.auth import Role
from app.db import get_db
from app.main import app
from app.models import Client, User

SIGNUP = {
    "email": "new.family@example.test",
    "password": "synthetic-pass-1",
    "name": "Synthetic New Family",
    "members": [
        {"nickname": "Mom", "age": 41, "restrictions": [], "conditions": ["E11"]},
        {"age": 6, "allergies": ["Nut Allergy"]},
    ],
}


def _client(database):
    app.dependency_overrides[get_db] = lambda: database
    return TestClient(app)


def test_signup_creates_pending_household_without_a_shopping_session(database):
    from app.models import ShoppingSession
    from app.services.nutrition import members_for

    try:
        response = _client(database).post("/auth/signup", json=SIGNUP)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    assert response.json()["Client_Enrollment_Status"] == "Pending"
    assert response.json()["Shopping_Session_Token"] is None  # Epic 1: no session until approved
    assert "session" in response.cookies  # signed in to the awaiting-approval screen
    client = database.query(Client).filter_by(Client_Enrollment_Status="Pending").all()[-1]
    assert database.query(ShoppingSession).filter_by(client_id=client.user_id).count() == 0
    members = client.members
    assert [m.nickname for m in members] == ["Mom", "Person 2"]
    assert json.loads(members[0].medical_profile.icd10_codes) == ["E11"]
    assert members_for(client)[0]["restrictions"] == [
        "Low Sugar"
    ]  # E11 -> Low Sugar via the matrix
    assert client.Dietary_Tier_ID == 9  # strictest member: Nut Allergy
    assert client.Household_Size == 2


def test_icd10_codes_are_stored_only_encrypted(database):
    try:
        _client(database).post("/auth/signup", json=SIGNUP)
    finally:
        app.dependency_overrides.clear()
    stored = (
        database.execute(text("SELECT icd10_codes FROM client_medical_profiles")).scalars().all()
    )
    assert stored and all("E11" not in value for value in stored)
    for (table,) in database.execute(text("SELECT name FROM sqlite_master WHERE type='table'")):
        for row in database.execute(text(f'SELECT * FROM "{table}"')):
            assert "E11" not in " ".join(str(value) for value in row), table


def test_signup_rejects_duplicate_email_and_unknown_condition(database):
    try:
        client = _client(database)
        first = client.post("/auth/signup", json=SIGNUP)
        duplicate = client.post("/auth/signup", json=SIGNUP)
        unknown = client.post(
            "/auth/signup",
            json={**SIGNUP, "email": "other@example.test", "members": [{"conditions": ["x"]}]},
        )
    finally:
        app.dependency_overrides.clear()
    assert first.status_code == 201
    assert duplicate.status_code == 409
    assert unknown.status_code == 422


def test_pending_can_sign_in_but_inactive_cannot(database):
    try:
        client = _client(database)
        pending = client.post(
            "/auth/login",
            json={"email": "client.pending@example.test", "password": "demo-password"},
        )
        inactive = client.post(
            "/auth/login",
            json={"email": "client.inactive@example.test", "password": "demo-password"},
        )
    finally:
        app.dependency_overrides.clear()
    assert pending.status_code == 200
    assert pending.json()["Client_Enrollment_Status"] == "Pending"
    assert pending.json()["Shopping_Session_Token"] is None
    assert inactive.status_code == 403


def test_me_has_no_real_name_and_household_can_be_edited(database, logged_in_client):
    cookies = logged_in_client(Role.CLIENT).cookies
    try:
        client = _client(database)
        me = client.get("/me", cookies=cookies).json()
        updated = client.put(
            "/me/household",
            cookies=cookies,
            json={"members": [{"nickname": "Solo", "restrictions": ["Vegan"]}]},
        )
    finally:
        app.dependency_overrides.clear()
    assert "name" not in me and me["client_id"]
    assert [m["nickname"] for m in me["members"]] == ["Person 1", "Little one"]
    assert updated.json()["members"] == [
        {
            "nickname": "Solo",
            "age": None,
            "restrictions": ["Vegan"],
            "allergies": [],
            "conditions": [],
        }
    ]
    user = database.query(User).filter(User.role == "Client").first()
    assert database.get(Client, user.id).Household_Size == 1


def test_me_session_returns_token_for_the_checkout_qr(database, logged_in_client):
    from app.models import ShoppingSession

    login = logged_in_client(Role.CLIENT)
    database.add(ShoppingSession(Shopping_Session_Token="synthetic-qr", client_id=login.user.id))
    database.commit()
    try:
        api = _client(database)
        mine = api.get("/me/session", cookies=login.cookies).json()
        staff = api.get("/me/session", cookies=logged_in_client(Role.VOLUNTEER).cookies)
    finally:
        app.dependency_overrides.clear()
    assert mine == {"Shopping_Session_Token": "synthetic-qr", "client_id": login.user.id}
    assert staff.status_code == 403
