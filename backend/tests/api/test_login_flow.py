from app.models import Role
from seed.load import SEED_PASSWORD
from seed.personas import PERSONAS, STAFF_USERS


def login(client, email, password=SEED_PASSWORD):
    return client.post("/auth/login", json={"email": email, "password": password})


def test_active_client_gets_session_token_and_cookie(seeded, client):
    response = login(client, PERSONAS[0]["email"])
    assert response.status_code == 200
    body = response.json()
    assert body["role"] == "Client" and body["Shopping_Session_Token"] and body["queue"] is None
    assert "session" in response.cookies
    assert client.get("/capacity").status_code == 403  # now logged in as a client


def test_login_twice_returns_same_session_and_counts_once(seeded, client):
    first = login(client, PERSONAS[0]["email"]).json()["Shopping_Session_Token"]
    assert login(client, PERSONAS[0]["email"]).json()["Shopping_Session_Token"] == first


def test_wrong_password_and_unknown_email_are_401(seeded, client):
    assert login(client, PERSONAS[0]["email"], "wrong").status_code == 401
    assert login(client, "nobody@example.test").status_code == 401


def test_non_active_client_gets_friendly_403(seeded, client):
    response = login(client, PERSONAS[4]["email"])  # Pending
    assert response.status_code == 403
    assert "enrollment" in response.json()["detail"]


def test_staff_login_has_role_and_no_session(seeded, client):
    body = login(client, STAFF_USERS[Role.VOLUNTEER]).json()
    assert body == {"role": "Volunteer", "Shopping_Session_Token": None, "queue": None}


def test_full_floor_queues_client_and_blocks_activation(seeded, client):
    from app.services import capacity
    capacity.set_max_capacity(seeded, 1, user_id=1)
    assert login(client, PERSONAS[1]["email"]).json()["Shopping_Session_Token"]
    client.cookies.clear()
    body = login(client, PERSONAS[0]["email"]).json()
    assert body["Shopping_Session_Token"] is None
    assert body["queue"]["status"] == "waiting" and body["queue"]["position"] == 1
    assert client.get("/recommendations").status_code == 404  # no active session
    client.cookies.clear()
    login(client, STAFF_USERS[Role.VOLUNTEER])
    counts = client.get("/capacity").json()
    assert counts == {"Active_Floor_Shoppers": 1, "Max_Floor_Capacity": 1, "Queue_Waiting": 1}


def test_logout_frees_spot_and_promotes_oldest(seeded, client):
    from app.services import capacity
    capacity.set_max_capacity(seeded, 1, user_id=1)
    login(client, PERSONAS[1]["email"])
    waiting = {}
    for n in (0, 2):
        other = client.__class__(client.app)
        waiting[n] = other
        assert login(other, PERSONAS[n]["email"]).json()["queue"]["status"] == "waiting"
    assert client.post("/auth/logout").status_code == 204
    assert waiting[0].get("/queue/me").json()["status"] == "ready"
    assert waiting[2].get("/queue/me").json() == {"status": "waiting", "position": 1,
                                                  "message": "The store is full right now. You are number 1 in line."}
    assert waiting[0].post("/queue/me").json()["Shopping_Session_Token"]


def test_me_returns_contract_client_with_tier(seeded, client):
    login(client, PERSONAS[1]["email"])
    body = client.get("/me").json()
    assert body["Household_Size"] == 1 and body["Client_Enrollment_Status"] == "Active"
    assert body["profile"]["Dietary_Tier_ID"] == 4
    assert {"Kidney Friendly", "Low Sugar"} <= set(body["profile"]["restrictions"])


def test_me_requires_login(seeded, client):
    assert client.get("/me").status_code == 401


def test_recommendations_after_login_use_household_size(seeded, client):
    login(client, PERSONAS[3]["email"])  # vegan + nut allergy, household 6
    recs = {r["name"]: r for r in client.get("/recommendations").json()}
    assert recs["Rolled Oats"]["suggested_qty"] == 6
    assert "Peanut Butter" not in recs
