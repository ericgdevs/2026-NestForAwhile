from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta
from enum import StrEnum

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError
from fastapi import Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.config import Settings
from app.db import get_db
from app.models import Client, HouseholdMember, User

password_hasher = PasswordHasher()
AUTH_COOKIE = "session"


class Role(StrEnum):
    CLIENT = "Client"
    VOLUNTEER = "Volunteer"
    WAREHOUSE_STAFF = "Warehouse Staff"
    WAREHOUSE_MANAGER = "Warehouse Manager"
    DIRECTOR = "Director"


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return password_hasher.verify(password_hash, password)
    except (VerificationError, ValueError):
        return False


def email_lookup_hash(email: str) -> str:
    return hashlib.sha256(email.strip().lower().encode()).hexdigest()


def authenticate_user(database: Session, email: str, password: str) -> User | None:
    user = database.scalar(select(User).where(User.email_hash == email_lookup_hash(email)))
    if user is None or not user.is_active or not verify_password(password, user.password_hash):
        return None
    return user


def create_access_token(user_id: int, role: Role, expires_delta: timedelta | None = None) -> str:
    expires = datetime.now(UTC) + (expires_delta or timedelta(minutes=30))
    payload = {"sub": str(user_id), "role": role.value, "exp": expires}
    return jwt.encode(payload, Settings.from_env().jwt_secret, algorithm="HS256")


def decode_access_token(token: str) -> dict[str, object]:
    try:
        return jwt.decode(token, Settings.from_env().jwt_secret, algorithms=["HS256"])
    except jwt.PyJWTError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        ) from error


def set_auth_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        AUTH_COOKIE,
        token,
        httponly=True,
        secure=Settings.from_env().cookie_secure,
        samesite="lax",
        max_age=1800,
    )


def get_current_user(request: Request, database: Session = Depends(get_db)) -> User:
    token = request.cookies.get(AUTH_COOKIE)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    payload = decode_access_token(token)
    try:
        user_id = int(payload["sub"])
    except (KeyError, TypeError, ValueError) as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        ) from error
    # One query pulls the user with their household, so later lookups hit the session's cache
    # instead of paying a database round trip each (about 100 ms apiece on a remote database).
    user = database.scalars(
        select(User)
        .options(
            joinedload(User.client).joinedload(Client.dietary_profile),
            joinedload(User.client)
            .joinedload(Client.members)
            .joinedload(HouseholdMember.medical_profile),
        )
        .where(User.id == user_id)
    ).unique().one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    return user


def require_roles(*allowed_roles: Role):
    def role_dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in {role.value for role in allowed_roles}:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission for this action",
            )
        return current_user

    return role_dependency
