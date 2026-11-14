from fastapi.testclient import TestClient

from app.main import app


def test_health_reports_status_and_ai_provider(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "groq")

    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "ai_provider": "groq",
        "ai_provider_status": "configured",
    }
