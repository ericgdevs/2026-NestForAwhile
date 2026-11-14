import os

from cryptography.fernet import Fernet

# Set before app modules read settings
os.environ.setdefault("FIELD_ENCRYPTION_KEY", Fernet.generate_key().decode())
os.environ.setdefault("JWT_SECRET", "test-secret-0123456789-0123456789")

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel

from app import models  # noqa: F401  (registers tables)
from app.db import get_session, make_engine
from app.main import app


@pytest.fixture
def session(tmp_path):
    engine = make_engine(f"sqlite:///{tmp_path / 'test.db'}")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


@pytest.fixture
def client(session):
    app.dependency_overrides[get_session] = lambda: session
    yield TestClient(app)
    app.dependency_overrides.clear()
