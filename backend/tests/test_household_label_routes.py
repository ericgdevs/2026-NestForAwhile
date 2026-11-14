import json

from fastapi.testclient import TestClient

from app.auth import Role
from app.db import get_db
from app.main import app
from app.models import Client

CRACKERS = "000000000004"  # synthetic tree-nut crackers


def _get(database, cookies, path):
    app.dependency_overrides[get_db] = lambda: database
    try:
        return TestClient(app).get(path, cookies=cookies)
    finally:
        app.dependency_overrides.clear()


def test_scan_is_yellow_with_who_and_allergy_when_one_member_is_allergic(
    database, logged_in_client
):
    cookies = logged_in_client(Role.CLIENT).cookies
    body = _get(database, cookies, f"/products/scan/{CRACKERS}").json()

    assert body["status"] == "Capped"
    assert body["not_for"] == [{"nickname": "Little one", "reason": "Nut Allergy"}]
    assert body["allergy_match"] is True


def test_scan_is_red_and_hidden_from_recommendations_when_everyone_is_restricted(
    database, logged_in_client
):
    login = logged_in_client(Role.CLIENT)
    for member in database.get(Client, login.user.id).members:
        member.allergies = json.dumps(["Nut Allergy"])
    database.commit()

    scan = _get(database, login.cookies, f"/products/scan/{CRACKERS}").json()
    picks = _get(database, login.cookies, "/recommendations").json()

    assert scan["status"] == "Restricted"
    assert "Synthetic Nut Crackers" not in {pick["name"] for pick in picks}


def test_red_scan_offers_safer_in_stock_swaps_with_location(database, logged_in_client):
    login = logged_in_client(Role.CLIENT)
    for member in database.get(Client, login.user.id).members:
        member.allergies = json.dumps(["Nut Allergy"])
    database.commit()

    red = _get(database, login.cookies, f"/products/scan/{CRACKERS}").json()
    green = _get(database, login.cookies, "/products/scan/000000000001").json()

    assert red["status"] == "Restricted"
    assert [swap["name"] for swap in red["swaps"]] == ["Synthetic Rolled Oats"]  # same category
    assert {"aisle", "shelf", "bin"} <= set(red["swaps"][0])
    assert green["swaps"] == []
