import json

import httpx
import pytest

from app.ai.provider import (
    MAX_COMPLETION_TOKENS,
    AITask,
    GroqProvider,
    MalformedOutput,
    OllamaProvider,
    ProviderError,
)
from app.ai.recipes import RECIPE_JSON_SCHEMA
from app.ai.schemas import ContextManifest

MANIFEST = ContextManifest(restrictions=[], items=[])


def test_ollama_provider_parses_structured_response(monkeypatch):
    monkeypatch.setenv("OLLAMA_MODEL", "synthetic")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://ollama")
    monkeypatch.setattr(
        "app.ai.provider.httpx.post",
        lambda url, **kwargs: httpx.Response(
            200,
            json={"done": True, "response": '{"recipes": []}'},
            request=httpx.Request("POST", url),
        ),
    )
    assert OllamaProvider().generate_json(AITask.RECIPES, MANIFEST) == {"recipes": []}


def test_groq_provider_requires_key(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with pytest.raises(ProviderError, match="GROQ_API_KEY"):
        GroqProvider().generate_json(AITask.RECIPES, MANIFEST)


def test_groq_provider_parses_json_response_with_default_model(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "synthetic")
    monkeypatch.delenv("GROQ_MODEL", raising=False)
    sent = {}

    def post(url, **kwargs):
        sent.update(kwargs["json"])
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": '{"recipes": []}'}}]},
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr("app.ai.provider.httpx.post", post)
    assert GroqProvider().generate_json(AITask.RECIPES, MANIFEST) == {"recipes": []}
    assert sent["model"] == "openai/gpt-oss-20b"
    assert "instructions" in sent["messages"][0]["content"]


def test_groq_retries_rate_limit_once_then_succeeds(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "synthetic")
    monkeypatch.setattr("app.ai.provider.time.sleep", lambda seconds: None)
    calls = []

    def post(url, **kwargs):
        calls.append(url)
        request = httpx.Request("POST", url)
        if len(calls) < 2:
            return httpx.Response(429, json={}, request=request)
        body = {"choices": [{"message": {"content": "{}"}}]}
        return httpx.Response(200, json=body, request=request)

    monkeypatch.setattr("app.ai.provider.httpx.post", post)
    assert GroqProvider().generate_json(AITask.RECIPES, MANIFEST) == {}
    assert len(calls) == 2  # one retry at most


def _ollama_post(monkeypatch, model, task=AITask.RECIPES, feedback=None, response=None):
    """Run OllamaProvider with a mocked HTTP call and return the request body it sent."""
    monkeypatch.setenv("OLLAMA_MODEL", model)
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://ollama")
    sent = {}

    def post(url, **kwargs):
        sent.update(kwargs["json"], url=url)
        body = response or {"done": True, "response": '{"recipes": []}'}
        return httpx.Response(200, json=body, request=httpx.Request("POST", url))

    monkeypatch.setattr("app.ai.provider.httpx.post", post)
    OllamaProvider().generate_json(task, MANIFEST, feedback)
    return sent


def test_ollama_recipes_send_the_strict_schema_and_instructions(monkeypatch):
    sent = _ollama_post(monkeypatch, "gpt-oss:20b", feedback="schema violation at recipes")
    assert sent["format"] == RECIPE_JSON_SCHEMA
    assert sent["stream"] is False
    assert sent["options"]["num_predict"] == MAX_COMPLETION_TOKENS
    assert "Create 1-6 safe recipes" in sent["prompt"]  # same instructions as Groq
    assert "schema violation at recipes" in sent["prompt"]  # same correction feedback


def test_ollama_gpt_oss_gets_low_reasoning_other_models_do_not(monkeypatch):
    assert _ollama_post(monkeypatch, "gpt-oss:20b")["think"] == "low"
    assert "think" not in _ollama_post(monkeypatch, "qwen3:8b")


def test_ollama_other_tasks_keep_plain_json_format(monkeypatch):
    plain = {"done": True, "response": "{}"}
    sent = _ollama_post(monkeypatch, "qwen3:8b", AITask.EXPLAIN, response=plain)
    assert sent["format"] == "json"


def test_ollama_length_stop_is_malformed_so_it_gets_one_retry(monkeypatch):
    truncated = {"done": True, "done_reason": "length", "response": '{"recipes": [{"ti'}
    with pytest.raises(MalformedOutput):
        _ollama_post(monkeypatch, "gpt-oss:20b", response=truncated)


def test_groq_request_is_unchanged_by_ollama_parity():
    body = GroqProvider.request_body("openai/gpt-oss-20b", AITask.RECIPES, "x")
    assert body["reasoning_effort"] == "low"
    assert body["response_format"]["json_schema"]["schema"] == RECIPE_JSON_SCHEMA


def _groq_400(code="json_validate_failed", message="Failed to generate JSON"):
    return {"error": {"code": code, "message": message}}


def _run_groq_recipes(monkeypatch, replies):
    """run_ai_task with Groq HTTP replies [(status, body)]; returns (result or error, calls)."""
    from types import SimpleNamespace

    monkeypatch.setenv("GROQ_API_KEY", "synthetic")
    calls = []

    def post(url, **kwargs):
        status, body = replies[len(calls)]
        calls.append(kwargs)
        return httpx.Response(status, json=body, request=httpx.Request("POST", url))

    monkeypatch.setattr("app.ai.provider.httpx.post", post)
    product = SimpleNamespace(
        id=1, sku="SYN-X-777", barcode="2999999999991", image_url=None,
        name="Rice", category="Grains",
        allergens=[], diet_flags=[], calories=1, sodium_mg=1, sugar_g=1, sat_fat_g=1,
        potassium_mg=1, protein_g=1,
    )  # fmt: skip
    from app.ai.orchestrator import AIOrchestrationError, run_ai_task

    try:
        return run_ai_task(AITask.RECIPES, [product], [], provider=GroqProvider()), len(calls)
    except AIOrchestrationError as exc:
        return exc, len(calls)


GOOD = {
    "choices": [{"message": {"content": json.dumps({"recipes": [
        {"title": "Bowl", "cuisine": "American",
         "ingredients": [{"name": "Rice", "product_id": 0}], "steps": ["Cook."]}
    ]})}}]
}  # fmt: skip


def test_groq_schema_400_is_retried_once_then_succeeds(monkeypatch):
    result, calls = _run_groq_recipes(monkeypatch, [(400, _groq_400()), (200, GOOD)])
    assert calls == 2 and result.output.recipes[0].title == "Bowl"


def test_groq_schema_400_twice_gives_up_after_one_retry(monkeypatch):
    result, calls = _run_groq_recipes(monkeypatch, [(400, _groq_400())] * 2)
    assert calls == 2 and "MalformedOutput" in str(result)


def test_groq_schema_message_without_code_is_also_retried(monkeypatch):
    body = _groq_400(code="", message="response failed JSON schema validation")
    assert _run_groq_recipes(monkeypatch, [(400, body), (200, GOOD)])[1] == 2


@pytest.mark.parametrize("body", [_groq_400("invalid_request_error", "bad model"), {}, "oops"])
def test_other_groq_400_is_a_hard_error_with_no_retry(monkeypatch, body):
    result, calls = _run_groq_recipes(monkeypatch, [(400, body), (200, GOOD)])
    assert calls == 1 and "ProviderError" in str(result) and "MalformedOutput" not in str(result)
