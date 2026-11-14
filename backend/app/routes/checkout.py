from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.auth import require_roles
from app.db import get_session
from app.models import Role, User
from app.schemas import CheckoutResult, InterventionCreate
from app.services import checkout

router = APIRouter(tags=["checkout"])
CHECKOUT_ROLES = (Role.VOLUNTEER, Role.MANAGER)


@router.post("/checkout/{session_token}/validate", response_model=CheckoutResult)
def validate_checkout(session_token: str, user: User = Depends(require_roles(*CHECKOUT_ROLES)),
                      session: Session = Depends(get_session)):
    return checkout.complete_checkout(session, session_token, user.id)


@router.post("/checkout/{session_token}/interventions")
def add_intervention(session_token: str, data: InterventionCreate, user: User = Depends(require_roles(*CHECKOUT_ROLES)),
                     session: Session = Depends(get_session)):
    checkout.record_intervention(session, session_token, user.id, data)
    return {}
