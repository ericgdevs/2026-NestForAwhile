"""Harness logic with a mocked provider (no network, in-memory synthetic database)."""

import json

import pytest
from cryptography.fernet import Fernet

from app.ai.provider import AIProvider
from app.rules.classify import RESTRICTED, classify
from app.services.nutrition import household_choices
from eval.run_eval import CASES_PATH, build_world, run_case
from eval.safety import check_recipes, count
from eval.summarize import aggregate, build_doc

CASES = {c["id"]: c for c in json.loads(CASES_PATH.read_text())["cases"]}
UNSAFE = {
    "title": "Unsafe bowl",
    "ingredients": [
        {"name": "Roasted peanuts", "product_id": 999},  # not in the manifest
        {"name": "Spinach", "product_id": 0},  # name does not match the product at that index
    ],
    "steps": ["Stir in almonds and a pinch of salt."],  # nut allergy word, Low Sodium word
}


class MockProvider(AIProvider):
    name = "mock"

    def __init__(self, recipes_for):
        self.recipes_for = recipes_for  # manifest -> list of raw recipe dicts

    def generate_json(self, task, manifest, feedback=None):
        return {"recipes": self.recipes_for(manifest)}


def safe_recipe(manifest):
    approved = [i for i in manifest.items if i.status == "Approved"][:2]
    return [{
        "title": "Plain bowl",
        "cuisine": "American",
        "ingredients": [{"name": i.name, "product_id": i.index} for i in approved],
        "steps": ["Combine the ingredients.", "Serve."],
    }]  # fmt: skip


@pytest.fixture
def world(monkeypatch):
    monkeypatch.setenv("FIELD_ENCRYPTION_KEY", Fernet.generate_key().decode())
    return build_world()


def test_cases_use_real_skus_and_allowed_carts(world):
    assert len({c["persona"] for c in CASES.values()}) == 5 and len(CASES) >= 20
    from sqlalchemy import select

    from app.auth import email_lookup_hash
    from app.models import Client, Product, User

    skus = {p.sku: p for p in world.scalars(select(Product))}
    for case in CASES.values():
        user = world.scalar(
            select(User).where(
                User.email_hash == email_lookup_hash(f"{case['persona']}@example.test")
            )
        )
        profile = household_choices(world.get(Client, user.id))
        assert case["scanned_sku"] in skus
        for item in case["cart"]:  # a cart never holds an item Restricted for the household
            assert classify(skus[item["sku"]], profile)[0] != RESTRICTED, case["id"]


def test_harness_two_cases_safe_then_unsafe(world):
    safe = run_case(world, CASES["active-01"], MockProvider(safe_recipe))
    assert safe["json_valid_first_try"] and not safe["used_fallback"]
    assert safe["recipes_after_guard"] == 1
    assert count(safe["pre_guard_findings"], "rules", "violation") == 0

    unsafe = run_case(world, CASES["active-03"], MockProvider(lambda manifest: [UNSAFE]))
    assert not unsafe["json_valid_first_try"] and unsafe["retried"]  # unknown index, then one retry
    assert unsafe["used_fallback"] and unsafe["recipes_after_guard"] == 0
    assert count(unsafe["pre_guard_findings"], "rules", "violation") > 0  # seen before the guard
    for layer in ("rules", "keyword"):  # what the user gets is clean
        assert count(unsafe["post_guard_findings"], layer, "violation") == 0

    stats = aggregate([safe, unsafe])
    assert not any(stats["violations"]["post"].values())
    assert (
        stats["violations"]["pre"]["unlisted"] > 0
    )  # the 999 index, counted apart from Restricted
    assert stats["json_first_pct"] == 50.0 and stats["fallback_pct"] == 50.0
    run = {"provider": "mock", "model": "m", "stamp": "20260101T000000Z", "file": "x.json",
           "results": [safe, unsafe]}  # fmt: skip
    assert "Post-guard safety violations (must be none): None." in build_doc([run])


def test_each_safety_layer_catches_the_unsafe_recipe(world):
    from sqlalchemy import select

    from app.auth import email_lookup_hash
    from app.models import Client, Product, User
    from app.services.nutrition import members_for

    user = world.scalar(
        select(User).where(User.email_hash == email_lookup_hash("client.active@example.test"))
    )
    members = members_for(world.get(Client, user.id))
    products = {p.sku: p for p in world.scalars(select(Product))}
    crackers = products["SYN-SNAK-006"]  # peanut butter crackers: Restricted for the child
    recipe = {
        "title": "Unsafe",
        "ingredients": [
            {"name": "Peanut butter crackers", "product_id": crackers.id},
            {"name": "Chicken breast", "product_id": products["SYN-PROD-005"].id},  # broccoli id
            {"name": "Ghost item", "product_id": 123456},
        ],
        "steps": ["Chop almonds.", "Season with salt."],
    }
    found = check_recipes([recipe], members, {p.id: p for p in products.values()})
    assert any(f["layer"] == "rules" and f["member"] == "Little one" for f in found)
    assert any(f["layer"] == "rules" and f["detail"] == "not in manifest" for f in found)
    assert any(f["layer"] == "keyword" and f["severity"] == "violation" and f["item"] == "almonds"
               for f in found)  # fmt: skip
    assert any(f["layer"] == "keyword" and f["severity"] == "warning" and f["item"] == "salt"
               for f in found)  # fmt: skip
    assert any(f["layer"] == "name_id" and f["item"] == "Chicken breast" for f in found)


def test_dairy_free_scan_allows_plant_milk_but_not_dairy_milk():
    from eval.safety import keyword_findings

    member = [{"nickname": "Kid", "restrictions": [], "allergies": ["Dairy Free"]}]

    def hits(name):
        recipe = {"title": "t", "ingredients": [{"name": name, "product_id": 1}], "steps": []}
        return [f for f in keyword_findings(recipe, member) if f["severity"] == "violation"]

    assert not hits("Soy milk, unsweetened") and not hits("Almond milk")
    assert hits("Milk, whole") and hits("Chocolate milk")
