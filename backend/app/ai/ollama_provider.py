from __future__ import annotations

from typing import Any

from app.config import Settings


class OllamaProvider:
    def __init__(self, settings: Settings):
        self.settings = settings

    def generate(self, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError("Ollama provider is implemented in T050")
