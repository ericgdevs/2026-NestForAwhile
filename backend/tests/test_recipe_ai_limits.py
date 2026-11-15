"""Recipe AI with the 135-product catalog: small manifest, one call, clean fallbacks."""

import json
import logging

import httpx
import pytest
from fastapi.testclient import TestClient

from app.ai.provider import AIProvider, AITask, GroqProvider, ProviderError
from app.ai.schemas import ContextManifest
from app.auth import Role
from app.db import get_db
from app.main import app
from app.models import AIRequest, Product
from app.routes.recipes import MANIFEST_EXTRAS, manifest_products


def post_recipes(database, logged_in_client, body=None):
    app.dependency_overrides[get_db] = lambda: database
    try:
        client = TestClient(app, cookies=logged_in_client(Role.CLIENT).cookies)
        return client.post("/recipes", json=body)
    finally:
        app.dependency_overrides.clear()


class RecordingProvider(AIProvider):
    name = "fake"

    def __init__(self):
        self.calls: list[tuple[AITask, ContextManifest]] = []

    def generate_json(self, task, manifest, feedback=None):
        self.calls.append((task, manifest))
        item = manifest.items[0]
        ingredient = {"name": item.name, "product_id": item.index}
        return {"recipes": [{"title": "Bowl", "ingredients": [ingredient], "steps": ["Mix."]}]}


def test_manifest_is_capped_with_the_full_catalog(database):
    products = {p.id: p for p in database.query(Product)}
    assert len(products) >= 135
    focus = next(p for p in products.values() if p.name == "Black beans, dry")
    cart = [{"product_id": next(iter(products))}]
    profile = {"restrictions": ["Low Sodium"], "allergies": []}

    chosen = manifest_products(products, cart, profile, focus.id)

    assert len(chosen) <= MANIFEST_EXTRAS + 2
    assert chosen[0].id == focus.id and chosen[1].id == cart[0]["product_id"]
    assert len({p.category for p in chosen}) >= 6  # varied, not 25 canned goods
    assert chosen[2].category == focus.category  # scanned item's category ranks first
    from app.ai.context_manifest import build_manifest

    manifest, _ = build_manifest(chosen, ["Low Sodium"])
    assert len(json.dumps(manifest.model_dump())) < 12_000  # full catalog was ~45 KB


def test_one_recipe_request_makes_one_successful_call(database, logged_in_client, monkeypatch):
    provider = RecordingProvider()
    monkeypatch.setattr("app.ai.orchestrator.get_provider", lambda: provider)
    body = post_recipes(database, logged_in_client).json()

    assert body["used_fallback"] is False and body["recipes"]
    assert [task for task, _ in provider.calls] == [AITask.RECIPES]  # no second call
    assert len(provider.calls[0][1].items) <= MANIFEST_EXTRAS
    assert not database.query(AIRequest).one().used_fallback


@pytest.fixture
def groq(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "synthetic")
    sleeps, calls = [], []
    monkeypatch.setattr("app.ai.provider.time.sleep", sleeps.append)

    def respond(*statuses, headers=None):
        queue = list(statuses)

        def post(url, **kwargs):
            calls.append(kwargs)
            status = queue.pop(0)
            body = {"choices": [{"message": {"content": "{}"}}]} if status == 200 else {}
            return httpx.Response(
                status, json=body, headers=headers, request=httpx.Request("POST", url)
            )

        monkeypatch.setattr("app.ai.provider.httpx.post", post)

    return respond, calls, sleeps


@pytest.mark.parametrize("status", [413, 400, 429])
def test_groq_errors_fall_back_without_crashing_or_leaking(
    status, groq, database, logged_in_client, caplog, monkeypatch
):
    # An earlier migration test runs alembic's fileConfig, which disables existing loggers.
    monkeypatch.setattr(logging.getLogger("app.routes.recipes"), "disabled", False)
    respond, calls, _ = groq
    respond(*([status] * 2))
    with caplog.at_level(logging.WARNING):
        response = post_recipes(database, logged_in_client)

    assert response.status_code == 200
    assert response.json()["used_fallback"] is True
    assert f"status={status}" in caplog.text and "ProviderError" in caplog.text
    assert "Black beans" not in caplog.text and "instructions" not in caplog.text
    assert len(calls) == (2 if status == 429 else 1)  # only 429 is retried, once


def test_429_is_retried_once_honouring_retry_after_capped_at_two_seconds(groq):
    respond, calls, sleeps = groq
    respond(429, 429, 200, headers={"retry-after": "9"})
    manifest = ContextManifest(restrictions=[], items=[])
    with pytest.raises(ProviderError, match="rate limited"):
        GroqProvider().generate_json(AITask.RECIPES, manifest)
    assert len(calls) == 2 and sleeps == [2.0]


def test_429_then_success_returns_the_output(groq):
    respond, calls, sleeps = groq
    respond(429, 200, headers={"retry-after": "0.5"})
    manifest = ContextManifest(restrictions=[], items=[])
    assert GroqProvider().generate_json(AITask.RECIPES, manifest) == {}
    assert len(calls) == 2 and sleeps == [0.5]
