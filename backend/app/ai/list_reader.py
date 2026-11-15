"""Read a photographed shopping list into items with a vision model; the photo is never stored."""

from __future__ import annotations

import json
import os
from typing import Annotated

import httpx
from pydantic import BaseModel, Field, StringConstraints

from app.ai.provider import OLLAMA_DEFAULT_URL, ProviderError


class ListItem(BaseModel):
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
    quantity: int = Field(default=1, ge=1, le=99)


class ListReading(BaseModel):
    items: list[ListItem] = Field(max_length=50)


class VisionNotConfigured(ProviderError):
    """No vision model is set up; the client should type the list instead."""


SCHEMA = ListReading.model_json_schema()
PROMPT = (
    "This is a photo of a handwritten or printed grocery list. "
    "Return only JSON matching this schema, with one entry per grocery item: "
    f"{json.dumps(SCHEMA)}. Use the item name as written and the quantity "
    "(1 if none is written). Ignore anything that is not a grocery item."
)


def _ask_groq(image_base64: str, media_type: str) -> str:
    model = (os.getenv("GROQ_VISION_MODEL") or "").strip()
    api_key = (os.getenv("GROQ_API_KEY") or "").strip()
    if not model or not api_key:
        raise VisionNotConfigured("GROQ_VISION_MODEL and GROQ_API_KEY must be configured")
    response = httpx.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": PROMPT},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{media_type};base64,{image_base64}"},
                        },
                    ],
                }
            ],
            # shortcut: json_object + Pydantic check; Groq's strict json_schema is model-specific
            "response_format": {"type": "json_object"},
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


def _ask_ollama(image_base64: str, media_type: str) -> str:
    model = (os.getenv("OLLAMA_VISION_MODEL") or "").strip()
    if not model:
        raise VisionNotConfigured("OLLAMA_VISION_MODEL must be configured")
    host = (os.getenv("OLLAMA_BASE_URL") or OLLAMA_DEFAULT_URL).strip().rstrip("/")
    response = httpx.post(
        f"{host}/api/generate",
        json={
            "model": model,
            "prompt": PROMPT,
            "images": [image_base64],
            "format": SCHEMA,
            "stream": False,
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["response"]


def read_list_photo(image_base64: str, media_type: str) -> list[ListItem]:
    """Ask the model, validate its JSON, retry once; ProviderError if it still fails."""
    provider = (os.getenv("AI_PROVIDER") or "ollama").strip().lower()
    ask = _ask_groq if provider == "groq" else _ask_ollama
    failure: Exception | None = None
    for _attempt in range(2):
        try:
            return ListReading.model_validate_json(ask(image_base64, media_type)).items
        except VisionNotConfigured:
            raise
        except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as exc:
            failure = exc  # ValueError covers invalid JSON and Pydantic validation errors
    # Only the exception type is kept: its text could echo model output about the list.
    raise ProviderError(f"Reading the list photo failed ({type(failure).__name__})") from failure
