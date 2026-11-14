import pytest

from app.ai.provider import AITask, GroqProvider, OllamaProvider, get_provider
from app.ai.schemas import ContextManifest


@pytest.mark.parametrize("value, cls", [("groq", GroqProvider), ("ollama", OllamaProvider), (" Groq ", GroqProvider)])
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


@pytest.mark.parametrize("cls", [GroqProvider, OllamaProvider])
def test_stubs_make_no_calls(cls):
    with pytest.raises(NotImplementedError):
        cls().generate_json(AITask.EXPLAIN, ContextManifest(restrictions=[], items=[]))


def test_provider_module_is_implementation_free():
    import app.ai.provider as module
    from pathlib import Path

    source = Path(module.__file__).read_text().lower()
    for forbidden in ("import httpx", "import requests", "import groq", "from groq", "api.groq", "localhost:11434", "prompt", "system message"):
        assert forbidden not in source
    assert not {"httpx", "groq", "requests"} & set(vars(module))


def test_provider_interface_cannot_be_instantiated_directly():
    from app.ai.provider import AIProvider

    with pytest.raises(TypeError):
        AIProvider()


def test_tasks_are_limited_to_the_four_allowed_roles():
    assert {t.value for t in AITask} == {"explain", "recipes", "missing_ingredients", "substitutions"}


def test_provider_error_is_a_runtime_error():
    from app.ai.provider import ProviderError

    assert issubclass(ProviderError, RuntimeError)
