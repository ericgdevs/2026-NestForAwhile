from __future__ import annotations

from typing import Any, Protocol

from app.config import Settings


class AIProvider(Protocol):
    def generate(self, prompt: str, schema: dict[str, Any]) -> dict[str, Any]: ...


def provider_from_settings(settings: Settings | None = None) -> AIProvider:
    selected = (settings or Settings.from_env()).ai_provider.lower()
    if selected == "ollama":
        from app.ai.ollama_provider import OllamaProvider

        return OllamaProvider(settings or Settings.from_env())
    if selected == "groq":
        from app.ai.groq_provider import GroqProvider

        return GroqProvider(settings or Settings.from_env())
    raise ValueError(f"Unsupported AI_PROVIDER: {selected}")
