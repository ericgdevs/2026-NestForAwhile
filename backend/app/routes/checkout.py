from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import Role, require_roles
from app.db import get_db
from app.models import Cart, CartItem, Checkout, Intervention, User
from app.services.checkout import complete_checkout, session_by_token, validate_checkout

router = APIRouter()


class InterventionRequest(BaseModel):
    product_id: int
    action: str
    note: str | None = None


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


@router.post("/checkout/{session_token}/interventions")
def intervention(
    session_token: str,
    payload: InterventionRequest,
    current_user: User = Depends(require_roles(Role.VOLUNTEER, Role.WAREHOUSE_MANAGER)),
    database: Session = Depends(get_db),
):
    if payload.action != "removed_item":
        raise HTTPException(status_code=422, detail="Only removed_item is supported")
    session = session_by_token(database, session_token)
    if session is None:
        raise HTTPException(status_code=404, detail="Active shopping session not found")
    cart = database.scalar(select(Cart).where(Cart.session_id == session.id))
    item = database.scalar(
        select(CartItem).where(
            CartItem.cart_id == cart.id,
            CartItem.product_id == payload.product_id,
        )
    ) if cart else None
    if item is None:
        raise HTTPException(status_code=404, detail="Cart item not found")
    checkout = Checkout(
        session_id=session.id,
        validated_by=current_user.id,
        status="blocked",
    )
    database.add(checkout)
    database.flush()
    database.add(
        Intervention(
            checkout_id=checkout.id,
            product_id=payload.product_id,
            volunteer_id=current_user.id,
            action=payload.action,
            note=payload.note,
        )
    )
    database.delete(item)
    database.commit()
    return {"status": "removed_item", "checkout_id": checkout.id}
