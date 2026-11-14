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
