from __future__ import annotations

from collections.abc import Callable, Generator
from dataclasses import dataclass

import pytest
from cryptography.fernet import Fernet
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.auth import Role, create_access_token
from app.db import Base
from app.models import User
from seed.load import seed_catalog, seed_users


@dataclass(frozen=True)
class LoggedInClient:
    user: User
    token: str
    cookies: dict[str, str]


@pytest.fixture
def database(tmp_path, monkeypatch: pytest.MonkeyPatch) -> Generator[Session, None, None]:
    monkeypatch.setenv("FIELD_ENCRYPTION_KEY", Fernet.generate_key().decode())
    monkeypatch.setenv("JWT_SECRET", "synthetic-test-secret")
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        seed_users(session)
        seed_catalog(session)
        yield session


@pytest.fixture
def users_by_role(database: Session) -> dict[Role, User]:
    return {role: database.query(User).filter(User.role == role.value).first() for role in Role}


@pytest.fixture
def logged_in_client(
    users_by_role: dict[Role, User],
) -> Callable[[Role], LoggedInClient]:
    def build(role: Role) -> LoggedInClient:
        user = users_by_role[role]
        token = create_access_token(user.id, role)
        return LoggedInClient(user=user, token=token, cookies={"session": token})

    return build


@pytest.fixture
def mock_ai_provider():
    from unittest.mock import MagicMock

    return MagicMock(name="mock_ai_provider")
