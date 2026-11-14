from __future__ import annotations

import json
from typing import Any

import httpx

from app.config import Settings


class OllamaProvider:
    def __init__(self, settings: Settings, client: httpx.Client | None = None):
        self.settings = settings
        self.client = client

    def generate(self, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        owns_client = self.client is None
        client = self.client or httpx.Client(timeout=30)
        try:
            response = client.post(
                f"{self.settings.ollama_base_url.rstrip('/')}/api/generate",
                json={
                    "model": self.settings.ollama_model,
                    "prompt": prompt,
                    "format": schema,
                    "stream": False,
                },
            )
            response.raise_for_status()
            payload = response.json()
            return payload["response"] if isinstance(payload["response"], dict) else json.loads(
                payload["response"]
            )
        finally:
            if owns_client:
                client.close()
