import os
from dataclasses import dataclass
from pathlib import Path


def _load_dotenv() -> None:
    env_file = Path(__file__).resolve().parents[2] / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


@dataclass(frozen=True)
class Settings:
    database_url: str
    jwt_secret: str
    jwt_expire_minutes: int
    cookie_secure: bool
    field_encryption_key: str


def get_settings() -> Settings:
    _load_dotenv()
    return Settings(
        database_url=os.getenv("DATABASE_URL", "sqlite:///./nest.db"),
        jwt_secret=os.getenv("JWT_SECRET", "dev-only-secret-change-me-0123456789"),
        jwt_expire_minutes=int(os.getenv("JWT_EXPIRE_MINUTES", "60")),
        cookie_secure=os.getenv("COOKIE_SECURE", "false").lower() == "true",
        field_encryption_key=os.getenv("FIELD_ENCRYPTION_KEY", ""),
    )
