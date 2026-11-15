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
