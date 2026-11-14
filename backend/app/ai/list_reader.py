"""Read a photographed shopping list into text lines with a vision model; never stored."""

from __future__ import annotations

import json
import os

import httpx

from app.ai.provider import OLLAMA_DEFAULT_URL, ProviderError

PROMPT = (
    "This is a photo of a handwritten or printed grocery list. "
    'Return JSON {"lines": [str]} with one entry per item, exactly as written. '
    "Ignore anything that is not a grocery item."
)
MAX_LINES = 50


def _lines(content: str) -> list[str]:
    try:
        lines = json.loads(content)["lines"]
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        raise ProviderError("Vision model returned an invalid list") from exc
    if not isinstance(lines, list) or not all(isinstance(line, str) for line in lines):
        raise ProviderError("Vision model returned an invalid list")
    return [line.strip()[:120] for line in lines if line.strip()][:MAX_LINES]


def read_list_photo(image_base64: str, media_type: str) -> list[str]:
    provider = (os.getenv("AI_PROVIDER") or "ollama").strip().lower()
    try:
        if provider == "groq":
            model = (os.getenv("GROQ_VISION_MODEL") or "").strip()
            api_key = (os.getenv("GROQ_API_KEY") or "").strip()
            if not model or not api_key:
                raise ProviderError("GROQ_VISION_MODEL and GROQ_API_KEY must be configured")
            image_url = f"data:{media_type};base64,{image_base64}"
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
                                {"type": "image_url", "image_url": {"url": image_url}},
                            ],
                        }
                    ],
                    "response_format": {"type": "json_object"},
                },
                timeout=30,
            )
            response.raise_for_status()
            return _lines(response.json()["choices"][0]["message"]["content"])
        model = (os.getenv("OLLAMA_VISION_MODEL") or "").strip()
        if not model:
            raise ProviderError("OLLAMA_VISION_MODEL must be configured")
        host = (os.getenv("OLLAMA_BASE_URL") or OLLAMA_DEFAULT_URL).strip().rstrip("/")
        response = httpx.post(
            f"{host}/api/generate",
            json={
                "model": model,
                "prompt": PROMPT,
                "images": [image_base64],
                "format": "json",
                "stream": False,
            },
            timeout=30,
        )
        response.raise_for_status()
        return _lines(response.json()["response"])
    except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as exc:
        raise ProviderError(f"Reading the list photo failed: {exc}") from exc
