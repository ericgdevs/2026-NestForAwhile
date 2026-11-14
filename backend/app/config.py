from __future__ import annotations

import os
from dataclasses import dataclass


def _as_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def _as_origins(value: str | None) -> list[str]:
    return [origin.strip() for origin in (value or "").split(",") if origin.strip()]


@dataclass(frozen=True)
class Settings:
    database_url: str = "sqlite:///./warehouse.db"
    jwt_secret: str = "change-me-in-development"
    field_encryption_key: str = ""
    ai_provider: str = "ollama"
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = ""
    groq_api_key: str = ""
    groq_model: str = ""
    usda_api_key: str = ""
    allowed_origins: list[str] | None = None
    cookie_secure: bool = False
    seed_demo_data: bool = False

    @classmethod
    def from_env(cls) -> Settings:
        return cls(
            database_url=os.getenv("DATABASE_URL", cls.database_url),
            jwt_secret=os.getenv("JWT_SECRET", cls.jwt_secret),
            field_encryption_key=os.getenv("FIELD_ENCRYPTION_KEY", cls.field_encryption_key),
            ai_provider=os.getenv("AI_PROVIDER", cls.ai_provider),
            ollama_base_url=os.getenv("OLLAMA_BASE_URL", cls.ollama_base_url),
            ollama_model=os.getenv("OLLAMA_MODEL", cls.ollama_model),
            groq_api_key=os.getenv("GROQ_API_KEY", cls.groq_api_key),
            groq_model=os.getenv("GROQ_MODEL", cls.groq_model),
            usda_api_key=os.getenv("USDA_API_KEY", cls.usda_api_key),
            allowed_origins=_as_origins(os.getenv("ALLOWED_ORIGINS")),
            cookie_secure=_as_bool(os.getenv("COOKIE_SECURE"), cls.cookie_secure),
            seed_demo_data=_as_bool(os.getenv("SEED_DEMO_DATA"), cls.seed_demo_data),
        )


settings = Settings.from_env()
