from sqlalchemy import text

from app.config import Settings
from app.db import build_engine


def test_settings_read_environment(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./test.db")
    monkeypatch.setenv("ALLOWED_ORIGINS", "http://a.test, http://b.test")
    monkeypatch.setenv("COOKIE_SECURE", "true")

    settings = Settings.from_env()

    assert settings.database_url == "sqlite:///./test.db"
    assert settings.allowed_origins == ["http://a.test", "http://b.test"]
    assert settings.cookie_secure is True


def test_sqlite_engine_can_connect():
    with build_engine("sqlite:///:memory:").connect() as connection:
        assert connection.execute(text("select 1")).scalar_one() == 1


def test_postgres_engine_reuses_connections_instead_of_opening_one_per_request():
    pool = build_engine("postgresql://user:pass@db.test:6543/app").pool  # builds lazily, no connect
    assert pool.size() == 5 and pool._pre_ping and pool._recycle == 240
