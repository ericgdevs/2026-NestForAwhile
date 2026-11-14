import json
from datetime import UTC, datetime, timedelta

from sqlmodel import select

from app.models import CartItem, InventoryLot, Role
from app.rules.tiers import TIERS
from app.services import analytics, checkout
from seed.personas import PERSONAS
from tests.unit.test_checkout_validation import add_product, start_with_cart


def _checkout(seeded, lines, recommended=()):
    shopping = start_with_cart(seeded, lines)
    for item in seeded.exec(select(CartItem).where(CartItem.product_id.in_(recommended))):
        item.from_recommendation = True
        seeded.add(item)
    seeded.commit()
    return checkout.complete_checkout(seeded, shopping.Shopping_Session_Token, user_id=1)


def test_empty_analytics_are_zero(login_as):
    body = login_as(Role.MANAGER).get("/analytics").json()
    assert body["visits_completed"] == 0 and body["recommendation_adoption_rate"] == 0
    assert set(body) == {"families_served", "visits_completed", "pounds_distributed", "inventory_usage",
                         "recommendation_adoption_rate", "waste_reduction"}


def test_completed_checkout_updates_metrics(login_as, seeded):
    seed_soon = analytics.get_analytics(seeded).waste_reduction.expiring_soon_lots
    rice = add_product(seeded, "Rice", 10, weight_lb=2.0, expires_in_days=3)  # expiring soon
    beans = add_product(seeded, "Beans", 10, weight_lb=1.0)
    assert _checkout(seeded, [(rice, 2), (beans, 2)], recommended=[rice.id]).status == "completed"
    body = login_as(Role.DIRECTOR).get("/analytics").json()
    assert (body["families_served"], body["visits_completed"], body["inventory_usage"]) == (1, 1, 4)
    assert body["pounds_distributed"] == 6.0
    assert body["recommendation_adoption_rate"] == 0.5
    assert body["waste_reduction"] == {"expiring_soon_lots": seed_soon + 1, "pounds_saved": 4.0}


def test_payload_has_no_identifiers(login_as, seeded):
    _checkout(seeded, [(add_product(seeded, "Rice", 5), 1)])
    payloads = [login_as(Role.MANAGER).get("/analytics").text, json.dumps(analytics.clients_by_tier(seeded)),
                json.dumps(analytics.checkout_history(seeded), default=str),
                json.dumps(analytics.inventory_by_category(seeded))]
    banned = [p["name"] for p in PERSONAS] + [p["email"] for p in PERSONAS] + ["@", "client", "email", "phone", "user_id"]
    assert not [b for b in banned for text in payloads if b.lower() in text.lower()]


def test_breakdowns(seeded):
    _checkout(seeded, [(add_product(seeded, "Rice", 5, weight_lb=1.0), 2)])
    by_category = analytics.inventory_by_category(seeded)
    assert by_category["x"] == {"on_hand": 3, "distributed": 2}
    tiers = analytics.clients_by_tier(seeded)
    assert sum(tiers.values()) == len(PERSONAS) and list(tiers) == [name for name, _ in TIERS.values()]  # tier order, counts only
    (day,) = analytics.checkout_history(seeded)
    assert (day["checkouts"], day["units"], day["pounds"]) == (1, 2, 2.0)


def test_analytics_roles(login_as):
    for role in (Role.CLIENT, Role.VOLUNTEER, Role.STAFF):
        assert login_as(role).get("/analytics").status_code == 403
