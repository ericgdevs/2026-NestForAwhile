from fastapi.testclient import TestClient

from app.auth import Role, email_lookup_hash, hash_password
from app.db import get_db
from app.main import app
from app.models import CapacitySetting, Client, User


def test_second_client_is_queued_and_manager_capacity_promotes(database, logged_in_client):
    setting = database.query(CapacitySetting).first()
    if setting is None:
        setting = CapacitySetting(Max_Floor_Capacity=1)
        database.add(setting)
    else:
        setting.Max_Floor_Capacity = 1
    user = User(
        email="client.two@example.test",
        email_hash=email_lookup_hash("client.two@example.test"),
        password_hash=hash_password("demo-password"),
        role=Role.CLIENT.value,
    )
    database.add(user)
    database.flush()
    database.add(
        Client(
            user_id=user.id,
            name="Synthetic Second Client",
            Household_Size=1,
            Client_Enrollment_Status="Active",
        )
    )
    database.commit()
    app.dependency_overrides[get_db] = lambda: database
    try:
        client = TestClient(app)
        first = client.post(
            "/auth/login",
            json={"email": "client.active@example.test", "password": "demo-password"},
        )
        second = client.post(
            "/auth/login",
            json={"email": "client.two@example.test", "password": "demo-password"},
        )
        assert first.status_code == 200
        assert second.json()["Shopping_Session_Token"] is None
        assert second.json()["queue"]["status"] == "waiting"
        manager = logged_in_client(Role.WAREHOUSE_MANAGER)
        promoted = client.put(
            "/capacity",
            json={"Max_Floor_Capacity": 2},
            cookies=manager.cookies,
        )
        assert promoted.status_code == 200
        queue = client.get(
            "/queue/me",
            cookies=logged_in_client(Role.CLIENT).cookies,
        )
        assert queue.status_code == 200
    finally:
        app.dependency_overrides.clear()
