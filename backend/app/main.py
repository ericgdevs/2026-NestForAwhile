import os

from fastapi import FastAPI

app = FastAPI(title="NestForAwhile MTG Warehouse API", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "ai_provider": os.getenv("AI_PROVIDER", "ollama"),
    }
