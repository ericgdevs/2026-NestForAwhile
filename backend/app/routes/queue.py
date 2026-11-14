from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import Role, require_roles
from app.db import get_db
from app.models import Client, User
from app.services.queue import claim_ready, queue_state

router = APIRouter()


@router.get("/queue/me")
def my_queue(
    current_user: User = Depends(require_roles(Role.CLIENT)),
    database: Session = Depends(get_db),
):
    return queue_state(database, current_user.id)


@router.post("/queue/me")
def claim_queue(
    current_user: User = Depends(require_roles(Role.CLIENT)),
    database: Session = Depends(get_db),
):
    client = database.get(Client, current_user.id)
    try:
        token = claim_ready(database, client)
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return {"role": current_user.role, "Shopping_Session_Token": token}
