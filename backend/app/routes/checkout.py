from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import Role, require_roles
from app.db import get_db
from app.models import User
from app.services.checkout import complete_checkout, session_by_token, validate_checkout

router = APIRouter()


@router.post("/checkout/{session_token}/validate")
def validate(
    session_token: str,
    current_user: User = Depends(require_roles(Role.VOLUNTEER, Role.WAREHOUSE_MANAGER)),
    database: Session = Depends(get_db),
):
    session = session_by_token(database, session_token)
    if session is None:
        raise HTTPException(status_code=404, detail="Active shopping session not found")
    errors = validate_checkout(database, session)
    return {"valid": not errors, "errors": errors}


@router.post("/checkout/{session_token}/complete")
def complete(
    session_token: str,
    current_user: User = Depends(require_roles(Role.VOLUNTEER, Role.WAREHOUSE_MANAGER)),
    database: Session = Depends(get_db),
):
    session = session_by_token(database, session_token)
    if session is None:
        raise HTTPException(status_code=404, detail="Active shopping session not found")
    try:
        checkout = complete_checkout(database, session, current_user)
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return {"checkout_id": checkout.id, "total_lb": checkout.total_lb}
