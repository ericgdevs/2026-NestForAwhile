from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.auth import Role, require_roles
from app.db import get_db
from app.models import Cart, CartItem, Client, Product, User
from app.services.cart import active_session, get_or_create_cart
from app.services.checkout import (
    ALLERGY_ACK,
    MANAGER_OVERRIDE,
    complete_checkout,
    record_intervention,
    review_checkout,
    session_by_token,
    validate_checkout,
)

router = APIRouter()
checkout_staff = require_roles(Role.VOLUNTEER, Role.WAREHOUSE_MANAGER)


class AddItemRequest(BaseModel):
    code: str = Field(min_length=1, max_length=64)  # SKU or barcode the volunteer scanned
    quantity: int = Field(default=1, ge=1, le=99)


class ProductNote(BaseModel):
    product_id: int
    note: str | None = Field(default=None, max_length=500)


def _session_or_404(database: Session, token: str):
    session = session_by_token(database, token)
    if session is None:
        raise HTTPException(status_code=404, detail="Active shopping session not found")
    return session


@router.get("/checkout/lookup")
def lookup(
    token: str | None = Query(default=None),
    client_id: int | None = Query(default=None),
    _: User = Depends(checkout_staff),
    database: Session = Depends(get_db),
):
    """Load a client's cart from the QR token on their phone, or the client ID they read out."""
    if token:
        session = session_by_token(database, token)
    elif client_id is not None:
        client = database.get(Client, client_id)
        session = active_session(database, client) if client else None
    else:
        raise HTTPException(status_code=422, detail="Scan the client's QR code or enter their ID")
    if session is None:
        raise HTTPException(status_code=404, detail="Active shopping session not found")
    return review_checkout(database, session)


@router.post("/checkout/{session_token}/items")
def volunteer_add_item(
    session_token: str,
    payload: AddItemRequest,
    current_user: User = Depends(checkout_staff),
    database: Session = Depends(get_db),
):
    """The client forgot to tap Add to cart: the volunteer scans it in (logged)."""
    session = _session_or_404(database, session_token)
    product = database.scalar(
        select(Product).where(or_(Product.sku == payload.code, Product.barcode == payload.code))
    )
    if product is None:
        raise HTTPException(status_code=404, detail="We couldn't find that product.")
    cart = get_or_create_cart(database, session)
    item = database.scalar(
        select(CartItem).where(CartItem.cart_id == cart.id, CartItem.product_id == product.id)
    )
    if item is None:
        database.add(CartItem(cart_id=cart.id, product_id=product.id, quantity=payload.quantity))
    else:
        item.quantity += payload.quantity
    record_intervention(database, session, current_user, product.id, "volunteer_added")
    database.commit()
    return review_checkout(database, session)


@router.delete("/checkout/{session_token}/items/{product_id}")
def volunteer_remove_item(
    session_token: str,
    product_id: int,
    current_user: User = Depends(checkout_staff),
    database: Session = Depends(get_db),
):
    session = _session_or_404(database, session_token)
    cart = database.scalar(select(Cart).where(Cart.session_id == session.id))
    item = (
        database.scalar(
            select(CartItem).where(CartItem.cart_id == cart.id, CartItem.product_id == product_id)
        )
        if cart
        else None
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Cart item not found")
    database.delete(item)
    record_intervention(database, session, current_user, product_id, "removed_item")
    database.commit()
    return review_checkout(database, session)


@router.post("/checkout/{session_token}/acknowledge")
def acknowledge_allergy(
    session_token: str,
    payload: ProductNote,
    current_user: User = Depends(checkout_staff),
    database: Session = Depends(get_db),
):
    """The volunteer confirmed an allergy item with the client in person."""
    session = _session_or_404(database, session_token)
    pending = {entry["product_id"] for entry in review_checkout(database, session)["needs_ack"]}
    if payload.product_id not in pending:
        raise HTTPException(status_code=409, detail="That item doesn't need an allergy check")
    record_intervention(
        database, session, current_user, payload.product_id, ALLERGY_ACK, payload.note
    )
    database.commit()
    return review_checkout(database, session)


@router.post("/checkout/{session_token}/override")
def manager_override(
    session_token: str,
    payload: ProductNote,
    current_user: User = Depends(require_roles(Role.WAREHOUSE_MANAGER)),
    database: Session = Depends(get_db),
):
    """A manager lets a Red item through; the reason is required and logged."""
    if not (payload.note or "").strip():
        raise HTTPException(status_code=422, detail="Write the reason for the override")
    session = _session_or_404(database, session_token)
    record_intervention(
        database, session, current_user, payload.product_id, MANAGER_OVERRIDE, payload.note
    )
    database.commit()
    return review_checkout(database, session)


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
    session = _session_or_404(database, session_token)
    errors = validate_checkout(database, session)
    return {"valid": not errors, "errors": errors, **review_checkout(database, session)}


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
    session = _session_or_404(database, session_token)
    cart = database.scalar(select(Cart).where(Cart.session_id == session.id))
    item = (
        database.scalar(
            select(CartItem).where(
                CartItem.cart_id == cart.id,
                CartItem.product_id == payload.product_id,
            )
        )
        if cart
        else None
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Cart item not found")
    entry = record_intervention(
        database, session, current_user, payload.product_id, payload.action, payload.note
    )
    database.delete(item)
    database.commit()
    checkout_id = entry.checkout_id
    return {"status": "removed_item", "checkout_id": checkout_id}
