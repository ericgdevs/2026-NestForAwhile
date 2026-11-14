import httpx
import pytest

from app.ai.groq_provider import GroqProvider
from app.ai.ollama_provider import OllamaProvider
from app.config import Settings


def test_ollama_provider_parses_structured_response():
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json={"response": '{"recipes": []}'})
    )
    with httpx.Client(transport=transport) as client:
        result = OllamaProvider(
            Settings(ollama_model="synthetic", ollama_base_url="http://ollama"),
            client,
        ).generate("prompt", {"type": "object"})
    assert result == {"recipes": []}


def test_groq_provider_requires_key():
    with pytest.raises(ValueError, match="GROQ_API_KEY"):
        GroqProvider(Settings(groq_model="synthetic")).generate("prompt", {})


def test_groq_provider_parses_json_response():
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            json={"choices": [{"message": {"content": '{"recipes": []}'}}]},
        )
    )
    with httpx.Client(transport=transport) as client:
        result = GroqProvider(
            Settings(groq_api_key="synthetic", groq_model="synthetic"),
            client,
        ).generate("prompt", {})
    assert result == {"recipes": []}
