"""Scanning a code we don't stock: Open Food Facts / USDA are always mocked here."""

import json

import httpx
import pytest
from fastapi.testclient import TestClient

from app.auth import Role
from app.db import get_db
from app.main import app
from app.models import Client, Product
from app.services import off, usda
from app.services.external_common import map_allergens

# client.active: "Person 1" (Low Sodium) and "Little one" (Nut Allergy)


def off_payload(**product):
    return {"status": 1, "product": {"product_name": "Synthetic Candy", **product}}


@pytest.fixture
def lookups(monkeypatch):
    """Route OFF through a mock transport; USDA finds nothing unless a test replaces it."""
    off._CACHE.clear()
    state = {"handler": lambda request: httpx.Response(200, json=off_payload())}

    def fake_off(code):
        transport = httpx.MockTransport(lambda request: state["handler"](request))
        with httpx.Client(transport=transport) as client:
            return off.lookup_open_food_facts(code, client)

    monkeypatch.setattr("app.services.nutrition.lookup_open_food_facts", fake_off)
    monkeypatch.setattr("app.services.nutrition.lookup_usda", lambda code: None)

    def reply(payload=None, status=200):
        state["handler"] = lambda request: httpx.Response(status, json=payload or {})

    return reply


def scan(database, logged_in_client, code):
    app.dependency_overrides[get_db] = lambda: database
    try:
        return TestClient(app).get(
            f"/products/scan/{code}", cookies=logged_in_client(Role.CLIENT).cookies
        )
    finally:
        app.dependency_overrides.clear()


def test_peanut_product_is_restricted_for_the_nut_allergy_member(
    database, logged_in_client, lookups
):
    lookups(
        off_payload(
            allergens_tags=["en:peanuts", "en:milk"],
            categories_tags=["en:snacks", "en:candies"],
            nutriments={"energy-kcal_100g": 480, "carbohydrates_100g": 65},
        )
    )
    body = scan(database, logged_in_client, "040000491804").json()

    assert body["status"] == "Restricted" and body["allergy_match"] is True
    assert body["not_for"] == [{"nickname": "Little one", "reason": "Nut Allergy"}]
    assert "Not for Little one: Nut Allergy." in body["explanation"]
    assert "Not stocked at Epic Cure today" in body["explanation"]
    assert body["product_id"] is None  # not addable
    assert 1 <= len(body["swaps"]) <= 3
    assert {swap["name"] for swap in body["swaps"]} <= {
        p.name for p in database.query(Product).filter_by(category="Snacks")
    }
    assert all(swap["status"] == "Approved" and swap["not_for"] == [] for swap in body["swaps"])
    assert (body["calories"], body["carbs_g"]) == (480, 65)


def test_traces_are_at_least_capped_with_the_reason(database, logged_in_client, lookups):
    lookups(off_payload(allergens_tags=[], traces_tags=["en:peanuts"], ingredients_text="Sugar"))
    body = scan(database, logged_in_client, "111").json()

    assert body["status"] == "Capped"
    assert "May contain traces of peanut" in body["explanation"]
    assert body["not_for"][0]["nickname"] == "Little one"


def test_missing_allergen_data_is_please_check_never_approved(database, logged_in_client, lookups):
    lookups(off_payload(nutriments={"sodium_100g": 0.045}))  # no allergen tags, no ingredients
    body = scan(database, logged_in_client, "222").json()
    assert body["status"] == "Capped"
    assert "couldn't confirm" in body["explanation"]


def test_a_clean_external_product_is_never_approved(database, logged_in_client, lookups):
    lookups(
        off_payload(
            ingredients_text="Oats, water",
            allergens_tags=[],
            nutriments={"sodium_100g": 0.01, "sugars_100g": 1, "saturated-fat_100g": 0},
        )
    )
    body = scan(database, logged_in_client, "333").json()
    assert body["status"] == "Capped" and "Not stocked at Epic Cure today" in body["explanation"]


def test_ingredient_text_catches_allergens_the_tags_missed(database, logged_in_client, lookups):
    lookups(off_payload(ingredients_text="Sugar, roasted PEANUTS, cocoa", allergens_tags=[]))
    assert scan(database, logged_in_client, "444").json()["status"] == "Restricted"


def test_sodium_in_grams_per_100g_becomes_milligrams(database, logged_in_client, lookups):
    lookups(off_payload(nutriments={"sodium_100g": 0.045, "potassium_100g": 0.2}))
    body = scan(database, logged_in_client, "555").json()
    assert body["sodium_mg"] == 45 and body["potassium_mg"] == 200


def test_serving_values_win_and_100g_scales_to_the_serving(monkeypatch):
    nutriments = {"sodium_serving": 0.1, "sodium_100g": 9, "sugars_100g": 60}
    assert off.serving_amount(nutriments, "sodium", 40, 1000) == 100  # per serving wins
    assert off.serving_amount(nutriments, "sugars", 40) == 24  # 60 g/100 g in a 40 g serving
    assert off.serving_amount(nutriments, "sugars", None) == 60  # no serving: per 100 g
    assert off.serving_amount(nutriments, "calories", 40) is None


def test_salt_stands_in_for_missing_sodium():
    off._CACHE.clear()
    payload = off_payload(nutriments={"salt_100g": 0.1125})  # 0.1125 / 2.5 g = 45 mg
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json=payload))
    with httpx.Client(transport=transport) as client:
        assert off.lookup_open_food_facts("666", client)["sodium_mg"] == 45


def test_calories_and_carbs_are_null_when_unknown_and_never_change_status(
    database, logged_in_client, lookups
):
    lookups(off_payload(allergens_tags=["en:peanuts"], nutriments={}))
    body = scan(database, logged_in_client, "777").json()
    assert body["calories"] is None and body["carbs_g"] is None
    assert body["status"] == "Restricted"


def test_stored_products_return_calories_and_carbs_without_changing_status(
    database, logged_in_client, monkeypatch
):
    monkeypatch.setattr(
        "app.services.nutrition.lookup_external",
        lambda code: pytest.fail("no outside lookup for a display-only gap"),
    )
    for member in database.get(Client, logged_in_client(Role.CLIENT).user.id).members:
        member.allergies = json.dumps(["Nut Allergy"])  # everyone: so nut items are Restricted
    database.commit()
    apples = database.query(Product).filter_by(sku="SYN-PROD-001").one()
    almonds = database.query(Product).filter_by(name="Almonds, raw").one()
    legacy = database.query(Product).filter_by(sku="SYN-OATS-001").one()

    apple_scan = scan(database, logged_in_client, apples.barcode).json()
    almond_scan = scan(database, logged_in_client, almonds.barcode).json()
    legacy_scan = scan(database, logged_in_client, legacy.barcode).json()

    assert (apple_scan["calories"], apple_scan["carbs_g"]) == (95, 25)
    assert almond_scan["status"] == "Restricted" and almond_scan["calories"] == 164
    assert {e["nickname"] for e in almond_scan["not_for"]} == {"Person 1", "Little one"}
    assert (legacy_scan["calories"], legacy_scan["carbs_g"]) == (None, None)  # unset stays null


def test_lookup_timeout_gives_a_clear_result_not_a_crash(database, logged_in_client, monkeypatch):
    def timeout(request):
        raise httpx.ReadTimeout("slow", request=request)

    def failing(code):
        with httpx.Client(transport=httpx.MockTransport(timeout)) as client:
            return off.lookup_open_food_facts(code, client)

    off._CACHE.clear()
    monkeypatch.setattr("app.services.nutrition.lookup_open_food_facts", failing)
    monkeypatch.setattr("app.services.nutrition.lookup_usda", lambda code: None)
    response = scan(database, logged_in_client, "888")
    body = response.json()
    assert response.status_code == 200
    assert body["status"] == "Capped" and "couldn't look this item up" in body["explanation"]
    assert body["product_id"] is None and body["swaps"] == []
    assert off._CACHE == {}  # failures are not cached


def test_unknown_code_is_still_a_404(database, logged_in_client, lookups):
    lookups({"status": 0}, status=404)
    assert scan(database, logged_in_client, "999").status_code == 404


def test_usda_is_used_when_open_food_facts_does_not_know_the_code(
    database, logged_in_client, lookups, monkeypatch
):
    lookups({"status": 0}, status=404)
    monkeypatch.setattr(
        "app.services.nutrition.lookup_usda",
        lambda code: {"name": "USDA Cookie", "calories": 150, "carbs_g": 20,
                      "allergens": ["contains_peanut"], "diet_flags": ["contains_peanut"],
                      "traces": [], "categories": ["Cookies"]},
    )  # fmt: skip
    body = scan(database, logged_in_client, "1010").json()
    assert body["status"] == "Restricted" and body["calories"] == 150


def test_allergen_mapping_covers_tags_text_and_traces():
    mapped = map_allergens(
        ["en:peanuts", "en:nuts", "en:milk", "en:gluten", "en:soybeans", "en:crustaceans"],
        ["en:eggs"],
        "Wheat flour, nutmeg. May contain fish.",
    )
    assert mapped["allergens"] == [
        "contains_dairy", "contains_peanut", "contains_shellfish", "contains_soy",
        "contains_tree_nut",
    ]  # fmt: skip
    assert "contains_gluten" in mapped["diet_flags"]
    assert mapped["traces"] == ["contains_egg", "contains_fish"]
    assert map_allergens(None, None, "Salt, nutmeg")["allergens"] == []
    assert map_allergens(None, None, None)["allergens"] is None  # no data is not "no allergens"


def test_open_food_facts_maps_energy_and_carbs():
    off._CACHE.clear()
    payload = off_payload(nutriments={"energy-kcal_100g": 250, "carbohydrates_100g": 40})
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json=payload))
    with httpx.Client(transport=transport) as client:
        result = off.lookup_open_food_facts("1212", client)
    assert (result["calories"], result["carbs_g"]) == (250, 40)


def test_usda_maps_energy_and_carbs_and_scales_to_the_serving(monkeypatch):
    monkeypatch.setenv("USDA_API_KEY", "synthetic-key")
    usda._CACHE.clear()
    food = {
        "description": "Synthetic USDA Food",
        "servingSize": 50,
        "servingSizeUnit": "g",
        "foodNutrients": [
            {"nutrientId": 1008, "value": 400},
            {"nutrientId": 1005, "value": 60},
            {"nutrientId": 1093, "value": 200},
        ],
    }
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json={"foods": [food]}))
    with httpx.Client(transport=transport) as client:
        result = usda.lookup_usda("1313", client)
    assert (result["calories"], result["carbs_g"], result["sodium_mg"]) == (200, 30, 100)
