from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import Role, require_roles
from app.db import get_db
from app.models import Client, User
from app.services.visit import check_in, visit_state

router = APIRouter()
client_only = require_roles(Role.CLIENT)


def _client(database: Session, user: User) -> Client:
    client = database.get(Client, user.id)
    if client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
    return client


@router.get("/me/visit")
def my_visit(user: User = Depends(client_only), database: Session = Depends(get_db)):
    return visit_state(database, _client(database, user))


@router.post("/me/check-in")
def my_check_in(user: User = Depends(client_only), database: Session = Depends(get_db)):
    return check_in(database, _client(database, user))
