from datetime import timedelta

import pytest
from fastapi import Depends, HTTPException

from app.auth import (COOKIE_NAME, create_access_token, decode_access_token, hash_password,
                      require_roles, verify_password)
from app.main import app
from app.models import Role, User


def test_wrong_password_rejected():
    h = hash_password("right")
    assert verify_password("right", h)
    assert not verify_password("wrong", h)


def test_expired_token_rejected():
    token = create_access_token(1, Role.CLIENT, expires_in=timedelta(seconds=-1))
    with pytest.raises(HTTPException) as e:
        decode_access_token(token)
    assert e.value.status_code == 401


@app.get("/_test/staff-only", dependencies=[Depends(require_roles(Role.STAFF))])
def _staff_only():
    return {"ok": True}


def _login_cookie(session, client, role):
    user = User(email="x@example.test", email_hash=f"h-{role.value}", password_hash="x", role=role)
    session.add(user)
    session.commit()
    client.cookies.set(COOKIE_NAME, create_access_token(user.id, role))


def test_wrong_role_gets_403(session, client):
    _login_cookie(session, client, Role.CLIENT)
    assert client.get("/_test/staff-only").status_code == 403


def test_right_role_allowed(session, client):
    _login_cookie(session, client, Role.STAFF)
    assert client.get("/_test/staff-only").status_code == 200
