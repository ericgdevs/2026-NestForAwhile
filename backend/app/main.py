from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import Settings
from app.routes.auth import router as auth_router
from app.routes.capacity import router as capacity_router

app = FastAPI(title="NestForAwhile MTG Warehouse API", version="0.1.0")
app.include_router(auth_router)
app.include_router(capacity_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "ai_provider": Settings.from_env().ai_provider,
    }


frontend_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if frontend_dist.is_dir():
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
