import pytest

from app.ai.provider import provider_from_settings
from app.config import Settings


@pytest.mark.parametrize("provider", ["ollama", "groq"])
def test_provider_factory_selects_configured_provider(provider):
    instance = provider_from_settings(Settings(ai_provider=provider))
    assert instance.__class__.__name__.lower().startswith(provider)


def test_provider_factory_rejects_unknown_provider():
    with pytest.raises(ValueError, match="Unsupported AI_PROVIDER"):
        provider_from_settings(Settings(ai_provider="unknown"))
