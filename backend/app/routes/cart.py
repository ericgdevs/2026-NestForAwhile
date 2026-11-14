from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import Role, require_roles
from app.db import get_db
from app.models import CartItem, Client, Product, User
from app.services.cart import active_session, build_manifest, get_or_create_cart

router = APIRouter()


class CartItemRequest(BaseModel):
    product_id: int
    quantity: int = Field(ge=1)


def client_cart(database: Session, user: User):
    client = database.get(Client, user.id)
    session = active_session(database, client) if client else None
    if session is None:
        raise HTTPException(status_code=409, detail="No active shopping session")
    return get_or_create_cart(database, session)


@router.get("/cart")
def get_cart(
    current_user: User = Depends(require_roles(Role.CLIENT)),
    database: Session = Depends(get_db),
):
    cart = client_cart(database, current_user)
    return {"items": build_manifest(database, cart)}


@router.post("/cart/items")
def add_cart_item(
    payload: CartItemRequest,
    current_user: User = Depends(require_roles(Role.CLIENT)),
    database: Session = Depends(get_db),
):
    cart = client_cart(database, current_user)
    product = database.get(Product, payload.product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    item = database.scalar(
        select(CartItem).where(CartItem.cart_id == cart.id, CartItem.product_id == product.id)
    )
    if item is None:
        item = CartItem(cart_id=cart.id, product_id=product.id, quantity=payload.quantity)
        database.add(item)
    else:
        item.quantity = payload.quantity
    database.commit()
    return {"items": build_manifest(database, cart)}


@router.patch("/cart/items/{product_id}")
def update_cart_item(
    product_id: int,
    payload: CartItemRequest,
    current_user: User = Depends(require_roles(Role.CLIENT)),
    database: Session = Depends(get_db),
):
    cart = client_cart(database, current_user)
    item = database.scalar(
        select(CartItem).where(CartItem.cart_id == cart.id, CartItem.product_id == product_id)
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Cart item not found")
    item.quantity = payload.quantity
    database.commit()
    return {"items": build_manifest(database, cart)}


@router.delete("/cart/items/{product_id}", status_code=204)
def remove_cart_item(
    product_id: int,
    current_user: User = Depends(require_roles(Role.CLIENT)),
    database: Session = Depends(get_db),
):
    cart = client_cart(database, current_user)
    item = database.scalar(
        select(CartItem).where(CartItem.cart_id == cart.id, CartItem.product_id == product_id)
    )
    if item:
        database.delete(item)
        database.commit()
