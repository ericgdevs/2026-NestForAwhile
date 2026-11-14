from __future__ import annotations

import json
import time
from typing import Any

import httpx

from app.config import Settings


class GroqProvider:
    def __init__(self, settings: Settings, client: httpx.Client | None = None):
        self.settings = settings
        self.client = client

    def generate(self, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        if not self.settings.groq_api_key:
            raise ValueError("GROQ_API_KEY is required for the Groq provider")
        owns_client = self.client is None
        client = self.client or httpx.Client(timeout=30)
        try:
            for attempt in range(3):
                response = client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {self.settings.groq_api_key}"},
                    json={
                        "model": self.settings.groq_model,
                        "messages": [{"role": "user", "content": prompt}],
                        "response_format": {"type": "json_object"},
                    },
                )
                if response.status_code != 429 or attempt == 2:
                    break
                time.sleep(0.1 * (2**attempt))
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            return content if isinstance(content, dict) else json.loads(content)
        finally:
            if owns_client:
                client.close()
