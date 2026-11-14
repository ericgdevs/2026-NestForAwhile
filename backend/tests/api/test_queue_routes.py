from app.models import Role
from app.services import queue, sessions
from tests.unit.test_queue import client_id


def test_queue_me_requires_client_and_membership(login_as):
    assert login_as(Role.VOLUNTEER).get("/queue/me").status_code == 403
    assert login_as(Role.CLIENT).get("/queue/me").status_code == 404


def test_queue_me_state_and_claim_flow(login_as, seeded):
    from app.services import capacity
    capacity.set_max_capacity(seeded, 1, user_id=1)
    sessions.start_session(seeded, client_id(seeded, 1))
    me = client_id(seeded, 0)  # persona1 is the Client login
    queue.join_queue(seeded, me)
    c = login_as(Role.CLIENT)
    assert c.get("/queue/me").json()["position"] == 1
    assert c.post("/queue/me").status_code == 409
    sessions.end_session(seeded, client_id(seeded, 1))
    assert c.get("/queue/me").json()["status"] == "ready"
    assert c.post("/queue/me").json()["Shopping_Session_Token"]
