import pytest

from app.ai.provider import GroqProvider, OllamaProvider, get_provider
from app.config import Settings


@pytest.mark.parametrize("provider", ["ollama", "groq"])
def test_provider_factory_selects_configured_provider(monkeypatch, provider):
    monkeypatch.setenv("AI_PROVIDER", provider)
    assert Settings.from_env().ai_provider == provider
    assert get_provider().name == provider
    assert isinstance(get_provider(), {"ollama": OllamaProvider, "groq": GroqProvider}[provider])


def test_provider_factory_rejects_unknown_provider(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "unknown")
    with pytest.raises(ValueError, match="AI_PROVIDER"):
        get_provider()
