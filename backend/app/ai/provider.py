import json
import os
from abc import ABC, abstractmethod
from enum import Enum

import httpx

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
        host = (os.getenv("OLLAMA_HOST") or "").strip().rstrip("/")
        model = (os.getenv("OLLAMA_MODEL") or "").strip()
        if not host or not model:
            raise ProviderError("OLLAMA_HOST and OLLAMA_MODEL must be configured")

        payload = json.dumps(
            {"task": task.value, "manifest": manifest.model_dump(mode="json")},
            separators=(",", ":"),
        )
        try:
            response = httpx.post(
                f"{host}/api/generate",
                json={"model": model, "prompt": payload, "format": "json", "stream": False},
                timeout=30,
            )
            response.raise_for_status()
        except (httpx.TimeoutException, httpx.RequestError, httpx.HTTPStatusError) as exc:
            raise ProviderError(f"Ollama request failed: {exc}") from exc

        try:
            body = response.json()
        except (json.JSONDecodeError, ValueError) as exc:
            raise ProviderError("Ollama returned malformed JSON") from exc
        if not isinstance(body, dict) or body.get("done") is not True:
            raise ProviderError("Ollama returned an invalid response")

        content = body.get("response")
        if content is None or (isinstance(content, str) and not content.strip()):
            raise ProviderError("Ollama response content is missing")
        if not isinstance(content, str):
            raise ProviderError("Ollama returned an invalid response")

        try:
            output = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ProviderError("Ollama returned malformed JSON") from exc
        if not isinstance(output, dict):
            raise ProviderError("Ollama returned an invalid response")
        return output


PROVIDERS = {"groq": GroqProvider, "ollama": OllamaProvider}


def get_provider() -> AIProvider:
    name = (os.getenv("AI_PROVIDER") or "").strip().lower()
    if name not in PROVIDERS:
        raise ValueError(f"AI_PROVIDER must be one of {sorted(PROVIDERS)}, got {name!r}")
    return PROVIDERS[name]()
