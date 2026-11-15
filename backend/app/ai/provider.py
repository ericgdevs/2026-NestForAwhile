import json
import os
import time
from abc import ABC, abstractmethod
from enum import Enum

import httpx

from app.ai.recipes import RECIPE_INSTRUCTIONS, RECIPE_JSON_SCHEMA
from app.ai.schemas import ContextManifest

GROQ_DEFAULT_MODEL = "openai/gpt-oss-20b"
GROQ_ATTEMPTS = 2  # one try plus a single retry on 429, never more
MAX_RETRY_WAIT = 2.0
MAX_COMPLETION_TOKENS = 3000  # recipe JSON is ~1-2k tokens; reasoning is kept short below
GPT_OSS_PREFIX = "openai/gpt-oss"  # reasoning models that support structured outputs
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

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code  # logged on fallback; never the prompt or response body


class MalformedOutput(ProviderError):
    """The model's text was cut off or is not a JSON object; worth one retry with feedback."""


class AIProvider(ABC):
    name: str

    @abstractmethod
    def generate_json(
        self, task: AITask, manifest: ContextManifest, feedback: str | None = None
    ) -> dict:
        """Return raw JSON output for a task; callers must pass it through validate_ai_output().

        `feedback` is the reason the previous answer was rejected (retry once)."""


def _payload(task: AITask, manifest: ContextManifest, feedback: str | None = None) -> str:
    body = {"task": task.value, "manifest": manifest.model_dump(mode="json")}
    if task is AITask.RECIPES:
        body["instructions"] = RECIPE_INSTRUCTIONS
    if feedback:
        body["correction"] = (
            f"Your previous JSON answer was rejected: {feedback}. "
            "Reply again with only the corrected JSON object, kept short."
        )
    return json.dumps(body, separators=(",", ":"))


def extract_json_object(text: str) -> object:
    """json.loads, tolerating code fences or text around the first JSON object."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        if start < 0:
            raise
        return json.JSONDecoder().raw_decode(text[start:])[0]


def _retry_wait(response: httpx.Response) -> float:
    """Seconds to wait after a 429: Retry-After if it is a number, else 1 s, capped at 2 s."""
    try:
        wait = float(response.headers.get("retry-after", 1.0))
    except ValueError:
        wait = 1.0
    return min(max(wait, 0.0), MAX_RETRY_WAIT)


class GroqProvider(AIProvider):
    name = "groq"
    last_finish_reason: str | None = None  # for logs only

    @staticmethod
    def request_body(model: str, task: AITask, content: str) -> dict:
        """Groq chat request. gpt-oss gets low, hidden reasoning (so it cannot eat max tokens)
        and strict structured outputs; other models keep plain json_object mode."""
        body: dict = {
            "model": model,
            "messages": [{"role": "user", "content": content}],
            "max_completion_tokens": MAX_COMPLETION_TOKENS,
            "response_format": {"type": "json_object"},
        }
        if model.startswith(GPT_OSS_PREFIX):
            body["reasoning_effort"] = "low"
            body["include_reasoning"] = False
            if task is AITask.RECIPES:
                body["response_format"] = {
                    "type": "json_schema",
                    "json_schema": {
                        "name": "recipes",
                        "strict": True,
                        "schema": RECIPE_JSON_SCHEMA,
                    },
                }
        return body

    def generate_json(
        self, task: AITask, manifest: ContextManifest, feedback: str | None = None
    ) -> dict:
        api_key = (os.getenv("GROQ_API_KEY") or "").strip()
        model = (os.getenv("GROQ_MODEL") or "").strip() or GROQ_DEFAULT_MODEL
        if not api_key:
            raise ProviderError("GROQ_API_KEY must be configured")

        body = self.request_body(model, task, _payload(task, manifest, feedback))
        try:
            for attempt in range(GROQ_ATTEMPTS):
                response = httpx.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json=body,
                    timeout=30,
                )
                if response.status_code != 429 or attempt == GROQ_ATTEMPTS - 1:
                    break
                time.sleep(_retry_wait(response))
        except (httpx.TimeoutException, httpx.RequestError) as exc:
            raise ProviderError(f"Groq request failed: {exc}") from exc

        if response.status_code == 429:
            raise ProviderError("Groq rate limited", 429)
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise ProviderError(f"Groq request failed: {exc}", response.status_code) from exc

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
        self.last_finish_reason = choice.get("finish_reason")
        content = choice["message"].get("content")
        if self.last_finish_reason == "length":  # cut off: truncated JSON is never parsed
            raise MalformedOutput("Groq output truncated (finish_reason=length)")
        if content is None or (isinstance(content, str) and not content.strip()):
            raise ProviderError("Groq response content is missing")
        if not isinstance(content, str):
            raise ProviderError("Groq returned an invalid response")

        try:
            output = extract_json_object(content)
        except json.JSONDecodeError as exc:
            raise MalformedOutput("Groq returned malformed JSON") from exc
        if not isinstance(output, dict):
            raise ProviderError("Groq returned an invalid response")
        return output


class OllamaProvider(AIProvider):
    name = "ollama"

    def generate_json(
        self, task: AITask, manifest: ContextManifest, feedback: str | None = None
    ) -> dict:
        host = (os.getenv("OLLAMA_BASE_URL") or OLLAMA_DEFAULT_URL).strip().rstrip("/")
        model = (os.getenv("OLLAMA_MODEL") or "").strip()
        if not model:
            raise ProviderError("OLLAMA_MODEL must be configured")

        payload = _payload(task, manifest, feedback)
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
