from fastapi import FastAPI

from app.config import Settings

app = FastAPI(title="NestForAwhile MTG Warehouse API", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "ai_provider": Settings.from_env().ai_provider,
    }
