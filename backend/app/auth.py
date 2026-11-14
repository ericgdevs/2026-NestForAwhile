import hashlib
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Cookie, Depends, HTTPException
from pwdlib import PasswordHash
from sqlmodel import Session

from app.config import get_settings
from app.db import get_session
from app.models import Role, User

COOKIE_NAME = "access_token"
_hasher = PasswordHash.recommended()  # Argon2


def email_digest(email: str) -> str:
    # shortcut: unkeyed SHA-256 for lookup, add a keyed HMAC if emails need stronger protection
    return hashlib.sha256(email.strip().lower().encode()).hexdigest()


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return _hasher.verify(password, password_hash)


def create_access_token(user_id: int, role: Role, expires_in: timedelta | None = None) -> str:
    settings = get_settings()
    expires_in = expires_in or timedelta(minutes=settings.jwt_expire_minutes)
    payload = {
        "sub": str(user_id),
        "role": role.value,
        "exp": datetime.now(timezone.utc) + expires_in,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, get_settings().jwt_secret, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Please sign in again.")


def get_current_user(
    access_token: str | None = Cookie(default=None),
    session: Session = Depends(get_session),
) -> User:
    if not access_token:
        raise HTTPException(status_code=401, detail="Please sign in.")
    user = session.get(User, int(decode_access_token(access_token)["sub"]))
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="Please sign in again.")
    return user


def require_roles(*roles: Role):
    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="You don't have access to this.")
        return user

    return checker
