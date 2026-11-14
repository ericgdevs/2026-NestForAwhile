from datetime import date

from fastapi import HTTPException
from sqlmodel import Session, select

from app.models import Cart, CartItem, Product, SessionStatus, ShoppingSession
from app.rules.classify import Status, classify
from app.schemas import CartItemRead
from app.services import fifo, profiles


def get_active_session(session: Session, token: str) -> ShoppingSession:
    shopping = session.exec(select(ShoppingSession).where(ShoppingSession.Shopping_Session_Token == token)).first()
    if shopping is None or shopping.status != SessionStatus.ACTIVE:
        raise HTTPException(404, "No active shopping session for that token.")
    return shopping


def cart_items(session: Session, shopping: ShoppingSession) -> list[CartItem]:
    cart = session.exec(select(Cart).where(Cart.session_id == shopping.id)).first()
    if cart is None:
        return []
    return list(session.exec(select(CartItem).where(CartItem.cart_id == cart.id).order_by(CartItem.product_id)))


def usable_quantity(session: Session, product_id: int, today: date | None = None) -> int:
    return sum(lot.quantity for lot in fifo.usable_lots_fifo(session, product_id, today))


def find_blocked_items(session: Session, shopping: ShoppingSession, today: date | None = None) -> list[CartItemRead]:
    """Re-classify every cart line; Restricted, unknown products and stock shortfalls stop checkout."""
    restrictions = profiles.rule_restrictions(profiles.get_dietary_profile(session, shopping.client_id))
    blocked = []
    for item in cart_items(session, shopping):
        product = session.get(Product, item.product_id)
        if product is None:
            blocked.append(CartItemRead(product_id=item.product_id, quantity=item.quantity))
            continue
        status = classify(product, restrictions).status
        if status == Status.RESTRICTED or usable_quantity(session, product.id, today) < item.quantity:
            blocked.append(CartItemRead(product_id=product.id, name=product.name, quantity=item.quantity,
                                        status=status.name.capitalize()))
    return blocked
