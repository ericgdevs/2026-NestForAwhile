from datetime import timedelta

import pytest
from fastapi import HTTPException

from app.auth import (
    Role,
    create_access_token,
    decode_access_token,
    hash_password,
    require_roles,
    verify_password,
)
from app.models import User


def test_wrong_password_is_rejected(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", "synthetic-secret")
    password_hash = hash_password("correct-password")

    assert verify_password("wrong-password", password_hash) is False
    assert verify_password("correct-password", password_hash) is True


def test_expired_token_is_rejected(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", "synthetic-secret")
    token = create_access_token(1, Role.CLIENT, timedelta(seconds=-1))

    with pytest.raises(HTTPException) as error:
        decode_access_token(token)

    assert error.value.status_code == 401


def test_wrong_role_is_forbidden():
    dependency = require_roles(Role.VOLUNTEER)

    with pytest.raises(HTTPException) as error:
        dependency(User(role=Role.CLIENT.value))

    assert error.value.status_code == 403
