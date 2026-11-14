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
from app.models import Role


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


@pytest.fixture
def seeded(session):
    from seed.load import seed_all
    seed_all(session)
    return session


@pytest.fixture
def login_as(seeded, client):
    """Log the shared test client in as the seeded user for a role."""
    from sqlmodel import select

    from app.auth import COOKIE_NAME, create_access_token, email_digest
    from app.models import User
    from seed.personas import CLIENT_ROLE_EMAIL, STAFF_USERS

    emails = {**STAFF_USERS, Role.CLIENT: CLIENT_ROLE_EMAIL}

    def _login(role):
        user = seeded.exec(select(User).where(User.email_hash == email_digest(emails[role]))).one()
        client.cookies.set(COOKIE_NAME, create_access_token(user.id, role))
        return client

    return _login


@pytest.fixture
def mock_ai():
    """Stand-in AI provider so tests never reach a real model."""
    from unittest.mock import MagicMock
    return MagicMock(name="mock_ai_provider")
