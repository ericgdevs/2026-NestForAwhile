from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth import (
    Role,
    authenticate_user,
    create_access_token,
    get_current_user,
    set_auth_cookie,
)
from app.db import get_db
from app.models import Client, User
from app.services.queue import end_client_session, queue_state
from app.services.sessions import start_session

router = APIRouter()


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/auth/login")
def login(payload: LoginRequest, response: Response, database: Session = Depends(get_db)):
    user = authenticate_user(database, payload.email, payload.password)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    result: dict[str, object] = {"role": user.role}
    if user.role == Role.CLIENT.value:
        client = database.get(Client, user.id)
        if client is None or client.Client_Enrollment_Status != "Active":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Client enrollment is not Active",
            )
        token = start_session(database, client)
        result["Shopping_Session_Token"] = token
        if token is None:
            result["queue"] = queue_state(database, client.user_id)
    set_auth_cookie(response, create_access_token(user.id, Role(user.role)))
    return result


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
        "name": client.name,
        "Household_Size": client.Household_Size,
        "Client_Enrollment_Status": client.Client_Enrollment_Status,
        "profile": {
            "restrictions": json.loads(profile.restrictions) if profile else [],
            "allergies": json.loads(profile.allergies) if profile else [],
            "preferences": json.loads(profile.preferences) if profile else [],
        },
    }
