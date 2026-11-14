import json
import os
import time
from abc import ABC, abstractmethod
from enum import Enum

import httpx

from app.ai.recipes import RECIPE_INSTRUCTIONS
from app.ai.schemas import ContextManifest

GROQ_DEFAULT_MODEL = "openai/gpt-oss-20b"
GROQ_ATTEMPTS = 3
OLLAMA_DEFAULT_URL = "http://127.0.0.1:11434"


class AITask(str, Enum):
    """The only things AI may do; statuses stay with the rules engine."""

    EXPLAIN = "explain"
    RECIPES = "recipes"
    MISSING_INGREDIENTS = "missing_ingredients"
    SUBSTITUTIONS = "substitutions"


class ProviderError(RuntimeError):
    """Runtime failure of a configured provider (timeout, rate limit, 5xx).

    Real clients raise this."""


class AIProvider(ABC):
    name: str

    @abstractmethod
    def generate_json(self, task: AITask, manifest: ContextManifest) -> dict:
        """Return raw JSON output for a task; callers must pass it through validate_ai_output()."""


def _payload(task: AITask, manifest: ContextManifest) -> str:
    body = {"task": task.value, "manifest": manifest.model_dump(mode="json")}
    if task is AITask.RECIPES:
        body["instructions"] = RECIPE_INSTRUCTIONS
    return json.dumps(body, separators=(",", ":"))


class GroqProvider(AIProvider):
    name = "groq"

    def generate_json(self, task: AITask, manifest: ContextManifest) -> dict:
        api_key = (os.getenv("GROQ_API_KEY") or "").strip()
        model = (os.getenv("GROQ_MODEL") or "").strip() or GROQ_DEFAULT_MODEL
        if not api_key:
            raise ProviderError("GROQ_API_KEY must be configured")

        payload = _payload(task, manifest)
        try:
            for attempt in range(GROQ_ATTEMPTS):
                response = httpx.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": payload}],
                        "response_format": {"type": "json_object"},
                    },
                    timeout=30,
                )
                if response.status_code != 429 or attempt == GROQ_ATTEMPTS - 1:
                    break
                time.sleep(0.1 * 2**attempt)  # exponential backoff on rate limits
        except (httpx.TimeoutException, httpx.RequestError) as exc:
            raise ProviderError(f"Groq request failed: {exc}") from exc

        if response.status_code == 429:
            raise ProviderError("Groq rate limited")
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise ProviderError(f"Groq request failed: {exc}") from exc

        try:
            body = response.json()
        except (json.JSONDecodeError, ValueError) as exc:
            raise ProviderError("Groq returned malformed JSON") from exc
        if (
            not isinstance(body, dict)
            or not isinstance(body.get("choices"), list)
            or not body["choices"]
        ):
            raise ProviderError("Groq returned an invalid response")

        choice = body["choices"][0]
        if not isinstance(choice, dict) or not isinstance(choice.get("message"), dict):
            raise ProviderError("Groq returned an invalid response")
        content = choice["message"].get("content")
        if content is None or (isinstance(content, str) and not content.strip()):
            raise ProviderError("Groq response content is missing")
        if not isinstance(content, str):
            raise ProviderError("Groq returned an invalid response")

        try:
            output = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ProviderError("Groq returned malformed JSON") from exc
        if not isinstance(output, dict):
            raise ProviderError("Groq returned an invalid response")
        return output


class OllamaProvider(AIProvider):
    name = "ollama"

    def generate_json(self, task: AITask, manifest: ContextManifest) -> dict:
        host = (os.getenv("OLLAMA_BASE_URL") or OLLAMA_DEFAULT_URL).strip().rstrip("/")
        model = (os.getenv("OLLAMA_MODEL") or "").strip()
        if not model:
            raise ProviderError("OLLAMA_MODEL must be configured")

        payload = _payload(task, manifest)
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
