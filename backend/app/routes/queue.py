from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.auth import require_roles
from app.db import get_session
from app.models import Role, User
from app.services import queue, sessions
from app.schemas import QueueState

router = APIRouter(tags=["queue"])


@router.get("/queue/me", response_model=QueueState)
def my_queue_state(user: User = Depends(require_roles(Role.CLIENT)), session: Session = Depends(get_session)):
    queue.refresh_queue(session)
    state = queue.queue_state(session, user.id)
    if state is None:
        raise HTTPException(404, "You are not in the line.")
    return state


@router.post("/queue/me")
def confirm_here(user: User = Depends(require_roles(Role.CLIENT)), session: Session = Depends(get_session)):
    shopping = sessions.claim_turn(session, user.id)
    return {"role": user.role, "Shopping_Session_Token": shopping.Shopping_Session_Token}
