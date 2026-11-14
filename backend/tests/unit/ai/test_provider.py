import json

import httpx
import pytest

from app.ai.provider import AITask, GroqProvider, OllamaProvider, ProviderError, get_provider
from app.ai.schemas import ContextManifest


@pytest.mark.parametrize(
    "value, cls", [("groq", GroqProvider), ("ollama", OllamaProvider), (" Groq ", GroqProvider)]
)
def test_factory_selects_provider(monkeypatch, value, cls):
    monkeypatch.setenv("AI_PROVIDER", value)
    assert isinstance(get_provider(), cls)


@pytest.mark.parametrize("value", ["openai", ""])
def test_factory_rejects_unknown_provider(monkeypatch, value):
    monkeypatch.setenv("AI_PROVIDER", value)
    with pytest.raises(ValueError, match="AI_PROVIDER"):
        get_provider()


def test_factory_rejects_unset(monkeypatch):
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    with pytest.raises(ValueError):
        get_provider()


def test_provider_module_does_not_import_groq_sdk():
    from pathlib import Path

    import app.ai.provider as module

    source = Path(module.__file__).read_text().lower()
    for forbidden in ("import groq", "from groq"):
        assert forbidden not in source


def test_provider_interface_cannot_be_instantiated_directly():
    from app.ai.provider import AIProvider

    with pytest.raises(TypeError):
        AIProvider()


def test_tasks_are_limited_to_the_four_allowed_roles():
    assert {t.value for t in AITask} == {
        "explain",
        "recipes",
        "missing_ingredients",
        "substitutions",
    }


def test_provider_error_is_a_runtime_error():
    assert issubclass(ProviderError, RuntimeError)


@pytest.fixture
def ollama_env(monkeypatch):
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://ollama.test:11434/")
    monkeypatch.setenv("OLLAMA_MODEL", "qwen-test")


@pytest.fixture
def manifest():
    return ContextManifest(restrictions=[], items=[])


def ollama_response(status_code=200, *, json_body=None, content=None):
    return httpx.Response(
        status_code,
        json=json_body,
        content=content,
        request=httpx.Request("POST", "http://ollama.test:11434/api/generate"),
    )


def test_ollama_returns_raw_structured_json(monkeypatch, ollama_env, manifest):
    captured = {}

    def post(url, **kwargs):
        captured["url"] = url
        captured.update(kwargs)
        return ollama_response(json_body={"done": True, "response": '{"text":"Use canned beans."}'})

    monkeypatch.setattr("app.ai.provider.httpx.post", post)

    assert OllamaProvider().generate_json(AITask.EXPLAIN, manifest) == {"text": "Use canned beans."}
    assert captured["url"] == "http://ollama.test:11434/api/generate"
    assert captured["json"]["model"] == "qwen-test"
    assert captured["json"]["format"] == "json"
    assert captured["json"]["stream"] is False
    assert json.loads(captured["json"]["prompt"]) == {
        "task": "explain",
        "manifest": manifest.model_dump(mode="json"),
    }
    assert captured["timeout"] == 30


def test_ollama_timeout_raises_provider_error(monkeypatch, ollama_env, manifest):
    monkeypatch.setattr(
        "app.ai.provider.httpx.post",
        lambda *args, **kwargs: (_ for _ in ()).throw(httpx.TimeoutException("slow")),
    )

    with pytest.raises(ProviderError, match="request failed"):
        OllamaProvider().generate_json(AITask.EXPLAIN, manifest)


def test_ollama_connection_failure_raises_provider_error(monkeypatch, ollama_env, manifest):
    monkeypatch.setattr(
        "app.ai.provider.httpx.post",
        lambda *args, **kwargs: (_ for _ in ()).throw(httpx.ConnectError("down")),
    )

    with pytest.raises(ProviderError, match="request failed"):
        OllamaProvider().generate_json(AITask.EXPLAIN, manifest)


def test_ollama_malformed_json_raises_provider_error(monkeypatch, ollama_env, manifest):
    monkeypatch.setattr(
        "app.ai.provider.httpx.post", lambda *args, **kwargs: ollama_response(content=b"not json")
    )

    with pytest.raises(ProviderError, match="malformed JSON"):
        OllamaProvider().generate_json(AITask.EXPLAIN, manifest)


def test_ollama_non_success_response_raises_provider_error(monkeypatch, ollama_env, manifest):
    monkeypatch.setattr(
        "app.ai.provider.httpx.post",
        lambda *args, **kwargs: ollama_response(500, json_body={"error": "failed"}),
    )

    with pytest.raises(ProviderError, match="request failed"):
        OllamaProvider().generate_json(AITask.EXPLAIN, manifest)


def test_ollama_missing_response_content_raises_provider_error(monkeypatch, ollama_env, manifest):
    monkeypatch.setattr(
        "app.ai.provider.httpx.post",
        lambda *args, **kwargs: ollama_response(json_body={"done": True}),
    )

    with pytest.raises(ProviderError, match="content is missing"):
        OllamaProvider().generate_json(AITask.EXPLAIN, manifest)


@pytest.mark.parametrize(
    "body",
    [
        {"done": False, "response": "{}"},
        {"done": True, "response": []},
        {"done": True, "response": "[]"},
    ],
)
def test_ollama_invalid_response_raises_provider_error(monkeypatch, ollama_env, manifest, body):
    monkeypatch.setattr(
        "app.ai.provider.httpx.post", lambda *args, **kwargs: ollama_response(json_body=body)
    )

    with pytest.raises(ProviderError, match="invalid response"):
        OllamaProvider().generate_json(AITask.EXPLAIN, manifest)


@pytest.fixture
def groq_env(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setenv("GROQ_MODEL", "llama-test")


def groq_response(status_code=200, *, json_body=None, content=None):
    return httpx.Response(
        status_code,
        json=json_body,
        content=content,
        request=httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions"),
    )


def test_groq_returns_raw_structured_json(monkeypatch, groq_env, manifest):
    captured = {}

    def post(url, **kwargs):
        captured["url"] = url
        captured.update(kwargs)
        return groq_response(
            json_body={"choices": [{"message": {"content": '{"text":"Use canned beans."}'}}]}
        )

    monkeypatch.setattr("app.ai.provider.httpx.post", post)

    assert GroqProvider().generate_json(AITask.EXPLAIN, manifest) == {"text": "Use canned beans."}
    assert captured["url"] == "https://api.groq.com/openai/v1/chat/completions"
    assert captured["headers"] == {"Authorization": "Bearer test-key"}
    assert captured["json"]["model"] == "llama-test"
    assert captured["json"]["response_format"] == {"type": "json_object"}
    assert json.loads(captured["json"]["messages"][0]["content"]) == {
        "task": "explain",
        "manifest": manifest.model_dump(mode="json"),
    }
    assert captured["timeout"] == 30


@pytest.mark.parametrize(
    ("exception", "message"),
    [
        (httpx.TimeoutException("slow"), "request failed"),
        (httpx.ConnectError("down"), "request failed"),
    ],
)
def test_groq_transport_failures_raise_provider_error(
    monkeypatch, groq_env, manifest, exception, message
):
    monkeypatch.setattr(
        "app.ai.provider.httpx.post", lambda *args, **kwargs: (_ for _ in ()).throw(exception)
    )

    with pytest.raises(ProviderError, match=message):
        GroqProvider().generate_json(AITask.EXPLAIN, manifest)


def test_groq_rate_limit_raises_provider_error(monkeypatch, groq_env, manifest):
    monkeypatch.setattr(
        "app.ai.provider.httpx.post",
        lambda *args, **kwargs: groq_response(429, json_body={"error": "limited"}),
    )

    with pytest.raises(ProviderError, match="rate limited"):
        GroqProvider().generate_json(AITask.EXPLAIN, manifest)


def test_groq_non_success_response_raises_provider_error(monkeypatch, groq_env, manifest):
    monkeypatch.setattr(
        "app.ai.provider.httpx.post",
        lambda *args, **kwargs: groq_response(500, json_body={"error": "failed"}),
    )

    with pytest.raises(ProviderError, match="request failed"):
        GroqProvider().generate_json(AITask.EXPLAIN, manifest)


def test_groq_malformed_json_raises_provider_error(monkeypatch, groq_env, manifest):
    monkeypatch.setattr(
        "app.ai.provider.httpx.post",
        lambda *args, **kwargs: groq_response(
            json_body={"choices": [{"message": {"content": "not json"}}]}
        ),
    )

    with pytest.raises(ProviderError, match="malformed JSON"):
        GroqProvider().generate_json(AITask.EXPLAIN, manifest)


def test_groq_missing_response_content_raises_provider_error(monkeypatch, groq_env, manifest):
    monkeypatch.setattr(
        "app.ai.provider.httpx.post",
        lambda *args, **kwargs: groq_response(json_body={"choices": [{"message": {}}]}),
    )

    with pytest.raises(ProviderError, match="content is missing"):
        GroqProvider().generate_json(AITask.EXPLAIN, manifest)
