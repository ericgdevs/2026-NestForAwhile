from __future__ import annotations

from cryptography.fernet import Fernet
from sqlalchemy import Text
from sqlalchemy.types import TypeDecorator

from app.config import Settings


def _fernet(key: str | None = None) -> Fernet:
    value = key or Settings.from_env().field_encryption_key
    if not value:
        raise RuntimeError("FIELD_ENCRYPTION_KEY is required for encrypted fields")
    try:
        return Fernet(value.encode())
    except ValueError as error:
        raise RuntimeError("FIELD_ENCRYPTION_KEY must be a valid Fernet key") from error


def encrypt_value(value: str, key: str | None = None) -> str:
    return _fernet(key).encrypt(value.encode()).decode()


def decrypt_value(value: str, key: str | None = None) -> str:
    return _fernet(key).decrypt(value.encode()).decode()


class EncryptedText(TypeDecorator[str]):
    impl = Text
    cache_ok = True

    def __init__(self, key: str | None = None):
        super().__init__()
        self.key = key

    def process_bind_param(self, value: str | None, dialect) -> str | None:
        return None if value is None else encrypt_value(value, self.key)

    def process_result_value(self, value: str | None, dialect) -> str | None:
        return None if value is None else decrypt_value(value, self.key)
