from app.models import Role
from app.services import sessions
from tests.unit.test_queue import client_id


def test_no_session_no_recommendations(login_as):
    assert login_as(Role.CLIENT).get("/recommendations").status_code == 404


def test_recommendations_match_contract_shape(login_as, seeded):
    sessions.start_session(seeded, client_id(seeded, 0))
    body = login_as(Role.CLIENT).get("/recommendations").json()
    assert body and set(body[0]) == {"product_id", "name", "suggested_qty", "rationale", "status"}


def test_staff_cannot_read_client_recommendations(login_as):
    assert login_as(Role.STAFF).get("/recommendations").status_code == 403
