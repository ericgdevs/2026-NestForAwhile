from cryptography.fernet import Fernet
from sqlalchemy.types import Text, TypeDecorator

from app.config import get_settings


def _fernet() -> Fernet:
    key = get_settings().field_encryption_key
    if not key:
        raise RuntimeError("FIELD_ENCRYPTION_KEY is not set")
    return Fernet(key.encode())


class EncryptedText(TypeDecorator):
    """Text column stored as Fernet ciphertext."""

    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        return None if value is None else _fernet().encrypt(value.encode()).decode()

    def process_result_value(self, value, dialect):
        return None if value is None else _fernet().decrypt(value.encode()).decode()
