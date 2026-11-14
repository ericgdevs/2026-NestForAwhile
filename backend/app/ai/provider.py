import os
from abc import ABC, abstractmethod
from enum import Enum

from app.ai.schemas import ContextManifest


class AITask(str, Enum):
    """The only things AI may do; statuses stay with the rules engine."""
    EXPLAIN = "explain"
    RECIPES = "recipes"
    MISSING_INGREDIENTS = "missing_ingredients"
    SUBSTITUTIONS = "substitutions"


class ProviderError(RuntimeError):
    """Runtime failure of a configured provider (timeout, rate limit, 5xx); real clients raise this."""


class AIProvider(ABC):
    name: str

    @abstractmethod
    def generate_json(self, task: AITask, manifest: ContextManifest) -> dict:
        """Return raw JSON output for a task; callers must pass it through validate_ai_output()."""


class GroqProvider(AIProvider):
    name = "groq"

    def generate_json(self, task: AITask, manifest: ContextManifest) -> dict:
        raise NotImplementedError("Groq client is not implemented yet (T051)")


class OllamaProvider(AIProvider):
    name = "ollama"

    def generate_json(self, task: AITask, manifest: ContextManifest) -> dict:
        raise NotImplementedError("Ollama client is not implemented yet (T050)")


PROVIDERS = {"groq": GroqProvider, "ollama": OllamaProvider}


def get_provider() -> AIProvider:
    name = (os.getenv("AI_PROVIDER") or "").strip().lower()
    if name not in PROVIDERS:
        raise ValueError(f"AI_PROVIDER must be one of {sorted(PROVIDERS)}, got {name!r}")
    return PROVIDERS[name]()
