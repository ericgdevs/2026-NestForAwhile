from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import (
    Role,
    authenticate_user,
    create_access_token,
    email_lookup_hash,
    get_current_user,
    hash_password,
    set_auth_cookie,
)
from app.db import get_db
from app.models import Client, User
from app.services.cart import active_session
from app.services.household import MemberIn, apply_household, household_view, validate_members
from app.services.queue import end_client_session, queue_state
from app.services.sessions import start_session

router = APIRouter()


class LoginRequest(BaseModel):
    email: str
    password: str


class SignupRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=8, max_length=128)
    name: str = Field(min_length=1, max_length=120)  # staff-only: shown on the approval screen
    members: list[MemberIn] = Field(min_length=1, max_length=20)


def _start_client_visit(database: Session, client: Client, result: dict[str, object]) -> None:
    """Epic 1: a shopping session starts only when Client_Enrollment_Status is Active."""
    result["Client_Enrollment_Status"] = client.Client_Enrollment_Status
    if client.Client_Enrollment_Status != "Active":
        result["Shopping_Session_Token"] = None  # Pending: signed in to an awaiting-approval screen
        return
    token = start_session(database, client)
    result["Shopping_Session_Token"] = token
    if token is None:
        result["queue"] = queue_state(database, client.user_id)


@router.post("/auth/login")
def login(payload: LoginRequest, response: Response, database: Session = Depends(get_db)):
    user = authenticate_user(database, payload.email, payload.password)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    result: dict[str, object] = {"role": user.role}
    if user.role == Role.CLIENT.value:
        client = database.get(Client, user.id)
        # Pending may sign in (no session, awaiting approval); expired/Inactive is rejected.
        if client is None or client.Client_Enrollment_Status not in {"Active", "Pending"}:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Client enrollment is not Active",
            )
        _start_client_visit(database, client, result)
    set_auth_cookie(response, create_access_token(user.id, Role(user.role)))
    return result


@router.post("/auth/signup", status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, response: Response, database: Session = Depends(get_db)):
    """Self sign-up: the account starts Pending; shopping starts after a manager approves it."""
    lookup = email_lookup_hash(payload.email)
    if database.scalar(select(User).where(User.email_hash == lookup)) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    try:
        validate_members(payload.members)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    user = User(
        email=payload.email.strip(),
        email_hash=lookup,
        password_hash=hash_password(payload.password),
        role=Role.CLIENT.value,
        is_active=True,
    )
    database.add(user)
    database.flush()
    client = Client(
        user_id=user.id,
        name=payload.name.strip(),
        Household_Size=len(payload.members),
        Client_Enrollment_Status="Pending",
    )
    database.add(client)
    apply_household(client, payload.members)
    database.commit()

    result: dict[str, object] = {"role": user.role}
    _start_client_visit(database, client, result)
    set_auth_cookie(response, create_access_token(user.id, Role.CLIENT))
    return result


@router.get("/me/session")
def my_session(
    current_user: User = Depends(get_current_user), database: Session = Depends(get_db)
):
    """What the checkout QR shows: the session token only, plus the client ID to read out."""
    if current_user.role != Role.CLIENT.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Clients only")
    client = database.get(Client, current_user.id)
    session = active_session(database, client) if client else None
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active visit")
    return {
        "Shopping_Session_Token": session.Shopping_Session_Token,
        "client_id": client.user_id,
    }


@router.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    response: Response,
    current_user: User = Depends(get_current_user),
    database: Session = Depends(get_db),
):
    if current_user.role == Role.CLIENT.value:
        end_client_session(database, current_user.id)
    response.delete_cookie("session")


@router.get("/me")
def me(current_user: User = Depends(get_current_user), database: Session = Depends(get_db)):
    if current_user.role != Role.CLIENT.value:
        return {"role": current_user.role}
    client = database.get(Client, current_user.id)
    profile = client.dietary_profile
    return {
        "role": current_user.role,
        "client_id": client.user_id,  # the real name stays on the manager's approval screen only
        "Household_Size": client.Household_Size,
        "Client_Enrollment_Status": client.Client_Enrollment_Status,
        "profile": {
            "restrictions": json.loads(profile.restrictions) if profile else [],
            "allergies": json.loads(profile.allergies) if profile else [],
            "preferences": json.loads(profile.preferences) if profile else [],
        },
        "members": household_view(client),
    }
