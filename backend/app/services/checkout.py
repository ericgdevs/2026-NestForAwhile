from datetime import date

from fastapi import HTTPException
from sqlalchemy import update
from sqlmodel import Session, select

from app.models import (Cart, CartItem, Checkout, CheckoutItem, Intervention, InventoryLot, Product, SessionStatus,
                        ShoppingSession, Visit, utcnow)
from app.rules.classify import Status, classify
from app.schemas import CartItemRead, CheckoutResult, InterventionCreate
from app.services import fifo, movements, profiles, queue


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


class StockConflict(Exception):
    """A lot changed under us between validation and decrement."""

    def __init__(self, product_id: int):
        self.product_id = product_id


def _checkout_row(session: Session, shopping: ShoppingSession, user_id: int) -> Checkout:
    """One checkout per session: blocked attempts and interventions attach to the same row."""
    row = session.exec(select(Checkout).where(Checkout.session_id == shopping.id)).first()
    if row is None:
        row = Checkout(session_id=shopping.id, validated_by=user_id, status="blocked")
        session.add(row)
        session.flush()
    return row


def _decrement_fifo(session: Session, checkout: Checkout, product: Product, quantity: int) -> int:
    """Take stock oldest lot first with a guarded UPDATE; returns the first lot used."""
    remaining, first_lot = quantity, None
    for lot in fifo.usable_lots_fifo(session, product.id):
        if remaining == 0:
            break
        take = min(remaining, lot.quantity)
        hit = session.execute(update(InventoryLot).where(InventoryLot.id == lot.id, InventoryLot.quantity >= take)
                              .values(quantity=InventoryLot.quantity - take))
        if hit.rowcount != 1:
            raise StockConflict(product.id)
        movements.log_movement(session, lot.id, -take, "checkout", checkout.id)
        first_lot = first_lot or lot.id
        remaining -= take
    if remaining:
        raise StockConflict(product.id)
    return first_lot


def complete_checkout(session: Session, token: str, user_id: int) -> CheckoutResult:
    """Hard-stop on any blocked line; otherwise decrement stock, log movements, write the receipt and end the session in one transaction."""
    shopping = get_active_session(session, token)
    items = cart_items(session, shopping)
    if not items:
        raise HTTPException(400, "The cart is empty.")
    blocked = find_blocked_items(session, shopping)
    if blocked:
        _checkout_row(session, shopping, user_id)
        session.commit()
        return CheckoutResult(status="blocked", blocked_items=blocked)

    restrictions = profiles.rule_restrictions(profiles.get_dietary_profile(session, shopping.client_id))
    try:
        checkout = _checkout_row(session, shopping, user_id)
        total_lb = 0.0
        for item in items:
            product = session.get(Product, item.product_id)
            lot_id = _decrement_fifo(session, checkout, product, item.quantity)
            session.add(CheckoutItem(checkout_id=checkout.id, product_id=product.id, lot_id=lot_id, quantity=item.quantity,
                                     status_at_checkout=classify(product, restrictions).status.name.capitalize()))
            total_lb += (product.weight_lb or 0) * item.quantity
        now = utcnow()
        checkout.status, checkout.total_lb, checkout.completed_at, checkout.validated_by = "completed", total_lb, now, user_id
        session.add(Visit(client_id=shopping.client_id, session_id=shopping.id, started_at=shopping.started_at,
                          completed_at=now, pounds_distributed=total_lb))
        shopping.status, shopping.ended_at = SessionStatus.COMPLETED, now
        session.add_all([checkout, shopping])
        session.commit()
    except StockConflict as conflict:
        session.rollback()
        product = session.get(Product, conflict.product_id)
        line = next(i for i in items if i.product_id == conflict.product_id)
        return CheckoutResult(status="blocked", blocked_items=[
            CartItemRead(product_id=product.id, name=product.name, quantity=line.quantity)])
    except Exception:
        session.rollback()
        raise
    queue.refresh_queue(session)
    return CheckoutResult(status="completed", receipt_id=checkout.id)


def record_intervention(session: Session, token: str, user_id: int, data: InterventionCreate) -> None:
    """Remove the item from the cart and log it so the cart can be validated again."""
    shopping = get_active_session(session, token)
    line = next((i for i in cart_items(session, shopping) if i.product_id == data.product_id), None)
    if line is None:
        raise HTTPException(404, "That item is not in the cart.")
    checkout = _checkout_row(session, shopping, user_id)
    session.add(Intervention(checkout_id=checkout.id, product_id=data.product_id, volunteer_id=user_id,
                             action=data.action, note=data.note))
    session.delete(line)
    session.commit()
