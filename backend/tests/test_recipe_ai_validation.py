"""Groq answers 200 but the output fails validation: reasoning controls, extraction, one retry."""

import json
import logging

import httpx
import pytest
from fastapi.testclient import TestClient

from app.ai.provider import AITask, GroqProvider, extract_json_object
from app.auth import Role
from app.db import get_db
from app.main import app
from app.models import Product
from app.rules.classify import household_label
from app.services.swaps import find_swaps

GOOD = {
    "recipes": [
        {
            "title": "Oat bowl",
            "cuisine": "American",
            "ingredients": [{"name": "Oats", "product_id": 0}],
            "steps": ["Mix."],
        }
    ]
}


@pytest.fixture
def groq(monkeypatch):
    """Queue (finish_reason, content) replies; returns (queue function, captured request bodies)."""
    monkeypatch.setenv("AI_PROVIDER", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "synthetic")
    monkeypatch.delenv("GROQ_MODEL", raising=False)  # default: openai/gpt-oss-20b
    bodies, replies = [], []

    def post(url, **kwargs):
        bodies.append(kwargs["json"])
        finish, content = replies.pop(0)
        payload = {"choices": [{"finish_reason": finish, "message": {"content": content}}]}
        return httpx.Response(200, json=payload, request=httpx.Request("POST", url))

    monkeypatch.setattr("app.ai.provider.httpx.post", post)

    def queue(*items):
        replies.extend(items)

    return queue, bodies


def recipes(database, logged_in_client):
    app.dependency_overrides[get_db] = lambda: database
    try:
        client = TestClient(app, cookies=logged_in_client(Role.CLIENT).cookies)
        return client.post("/recipes").json()
    finally:
        app.dependency_overrides.clear()


def test_valid_json_returns_recipes_with_reasoning_controls_and_structured_output(
    groq, database, logged_in_client
):
    queue, bodies = groq
    queue(("stop", json.dumps(GOOD)))
    body = recipes(database, logged_in_client)

    assert body["used_fallback"] is False and body["recipes"][0]["title"] == "Oat bowl"
    sent = bodies[0]
    assert sent["reasoning_effort"] == "low" and sent["include_reasoning"] is False
    assert sent["max_completion_tokens"] >= 2000
    assert sent["response_format"]["type"] == "json_schema"
    assert sent["response_format"]["json_schema"]["strict"] is True
    assert len(bodies) == 1


def test_other_models_keep_plain_json_mode(monkeypatch):
    body = GroqProvider.request_body("llama-test", AITask.RECIPES, "{}")
    assert body["response_format"] == {"type": "json_object"}
    assert "reasoning_effort" not in body and "include_reasoning" not in body


def test_json_in_code_fences_or_with_text_around_it_is_parsed(groq, database, logged_in_client):
    queue, bodies = groq
    queue(("stop", "Here you go:\n```json\n" + json.dumps(GOOD) + "\n```"))
    assert recipes(database, logged_in_client)["used_fallback"] is False
    assert len(bodies) == 1
    assert extract_json_object('x {"a": {"b": 1}} trailing') == {"a": {"b": 1}}


def test_truncated_json_is_retried_once_then_falls_back(
    groq, database, logged_in_client, caplog, monkeypatch
):
    monkeypatch.setattr(logging.getLogger("app.ai.orchestrator"), "disabled", False)
    monkeypatch.setattr(logging.getLogger("app.routes.recipes"), "disabled", False)
    queue, bodies = groq
    queue(("length", '{"recipes": [{"title": "Oat'), ("length", '{"recipes": [{"title": "Oat'))
    with caplog.at_level(logging.WARNING):
        body = recipes(database, logged_in_client)

    assert body["used_fallback"] is True and len(bodies) == 2  # one retry, no more
    assert "correction" in bodies[1]["messages"][0]["content"]
    assert "finish_reason=length" in caplog.text
    assert "Oat" not in caplog.text  # never the model's text


def test_truncated_then_valid_recovers_on_the_retry(groq, database, logged_in_client):
    queue, bodies = groq
    queue(("length", '{"recipes": ['), ("stop", json.dumps(GOOD)))
    assert recipes(database, logged_in_client)["used_fallback"] is False
    assert len(bodies) == 2


def test_validation_error_is_retried_with_field_names_then_falls_back(
    groq, database, logged_in_client, caplog, monkeypatch
):
    monkeypatch.setattr(logging.getLogger("app.ai.orchestrator"), "disabled", False)
    bad = json.loads(json.dumps(GOOD))
    bad["recipes"][0]["ingredients"][0]["product_id"] = "0"  # StrictInt: a string is rejected
    queue, bodies = groq
    queue(("stop", json.dumps(bad)), ("stop", json.dumps(bad)))
    with caplog.at_level(logging.WARNING):
        body = recipes(database, logged_in_client)

    assert body["used_fallback"] is True and len(bodies) == 2
    retry_message = bodies[1]["messages"][0]["content"]
    assert "recipes.0.ingredients.0.product_id" in retry_message
    assert "recipes.0.ingredients.0.product_id" in caplog.text and "Mix." not in caplog.text


def test_rules_guard_still_applies_to_valid_ai_output(groq, database, logged_in_client):
    """Schema-valid JSON is still filtered: a recipe with an unlisted ingredient is dropped."""
    unlisted = {
        **GOOD["recipes"][0],
        "title": "Salty bowl",
        "ingredients": [{"name": "Salt", "product_id": None}],
    }
    queue, _ = groq
    queue(("stop", json.dumps({"recipes": [GOOD["recipes"][0], unlisted]})))
    body = recipes(database, logged_in_client)

    assert body["used_fallback"] is False
    assert [recipe["title"] for recipe in body["recipes"]] == ["Oat bowl"]


def test_swaps_are_only_items_approved_for_everyone(database):
    low_sodium = [{"nickname": "P1", "age": 40, "restrictions": ["Low Sodium"], "allergies": []}]
    chips = database.query(Product).filter_by(name="Potato chips, salted").one()
    assert household_label(chips, low_sodium)["status"] == "Capped"  # 148 mg is above 140

    swaps = find_swaps(database, chips, low_sodium, limit=50)
    by_name = {p.name: p for p in database.query(Product)}
    assert swaps and "Potato chips, salted" not in {s["name"] for s in swaps}
    assert all(s["status"] == "Approved" for s in swaps)
    assert all(
        household_label(by_name[s["name"]], low_sodium)["status"] == "Approved" for s in swaps
    )


def test_fewer_swaps_beat_unsafe_ones(database):
    strict = [
        {
            "nickname": "P1",
            "age": 40,
            "restrictions": ["Low Sodium", "Low Sugar", "Kidney Friendly", "Heart Healthy"],
            "allergies": ["Nut Allergy", "Dairy Free"],
        }
    ]
    drink = database.query(Product).filter_by(name="Cola soda").one()
    swaps = find_swaps(database, drink, strict, limit=50)
    assert all(s["status"] == "Approved" for s in swaps)
    assert len(swaps) < database.query(Product).filter_by(category="Beverages").count() - 1
