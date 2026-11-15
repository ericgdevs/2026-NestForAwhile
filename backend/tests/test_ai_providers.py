import httpx
import pytest

from app.ai.provider import AITask, GroqProvider, OllamaProvider, ProviderError
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
