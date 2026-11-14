from app.models import QueueEntry, QueueStatus, Role, SessionStatus, ShoppingSession


def test_capacity_counts_active_sessions_and_ready_entries(login_as, seeded):
    seeded.add(ShoppingSession(Shopping_Session_Token="t1", client_id=1, status=SessionStatus.ACTIVE))
    seeded.add(ShoppingSession(Shopping_Session_Token="t2", client_id=2, status=SessionStatus.COMPLETED))
    seeded.add(QueueEntry(client_id=3, status=QueueStatus.READY))
    seeded.add(QueueEntry(client_id=4, status=QueueStatus.WAITING))
    seeded.commit()
    body = login_as(Role.VOLUNTEER).get("/capacity").json()
    assert body["Active_Floor_Shoppers"] == 2
    assert body["Queue_Waiting"] == 1
    assert body["Max_Floor_Capacity"] >= 1


def test_capacity_hidden_from_clients_and_director(login_as):
    assert login_as(Role.CLIENT).get("/capacity").status_code == 403
    assert login_as(Role.DIRECTOR).get("/capacity").status_code == 403


def test_only_manager_sets_capacity_and_minimum_is_one(login_as):
    assert login_as(Role.STAFF).put("/capacity", json={"Max_Floor_Capacity": 5}).status_code == 403
    manager = login_as(Role.MANAGER)
    assert manager.put("/capacity", json={"Max_Floor_Capacity": 0}).status_code == 422
    assert manager.put("/capacity", json={"Max_Floor_Capacity": 7}).json()["Max_Floor_Capacity"] == 7
