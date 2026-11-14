from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth import Role, require_roles
from app.db import get_db
from app.models import Client, User
from app.services.household import MemberIn, apply_household, household_view

router = APIRouter()


class HouseholdRequest(BaseModel):
    members: list[MemberIn] = Field(min_length=1, max_length=20)


def _client(database: Session, user: User) -> Client:
    client = database.get(Client, user.id)
    if client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
    return client


@router.get("/me/household")
def get_household(
    current_user: User = Depends(require_roles(Role.CLIENT)),
    database: Session = Depends(get_db),
):
    return {"members": household_view(_client(database, current_user))}


@router.put("/me/household")
def put_household(
    payload: HouseholdRequest,
    current_user: User = Depends(require_roles(Role.CLIENT)),
    database: Session = Depends(get_db),
):
    client = _client(database, current_user)
    try:
        apply_household(client, payload.members)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    database.commit()
    return {"members": household_view(client)}
