from __future__ import annotations

from datetime import UTC, date, datetime

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models import (
    Cart,
    CartItem,
    Checkout,
    CheckoutItem,
    Client,
    InventoryLot,
    InventoryMovement,
    ShoppingSession,
    User,
    Visit,
)
from app.rules.classify import RESTRICTED, classify
from app.services import queue


def session_by_token(database: Session, token: str) -> ShoppingSession | None:
    return database.scalar(
        select(ShoppingSession).where(
            ShoppingSession.Shopping_Session_Token == token,
            ShoppingSession.status == "active",
        )
    )


def validate_checkout(database: Session, session: ShoppingSession) -> list[str]:
    cart = database.scalar(select(Cart).where(Cart.session_id == session.id))
    if cart is None:
        return ["Cart is empty."]
    client = database.get(Client, session.client_id)
    profile = client.dietary_profile if client else None
    profile_data = {"restrictions": [], "allergies": []}
    if profile:
        import json

        profile_data = {
            "restrictions": json.loads(profile.restrictions),
            "allergies": json.loads(profile.allergies),
        }
    errors = []
    for item in database.scalars(select(CartItem).where(CartItem.cart_id == cart.id)):
        lots = database.scalars(
            select(InventoryLot)
            .where(
                InventoryLot.product_id == item.product_id,
                InventoryLot.quantity > 0,
                InventoryLot.expiration_date >= date.today(),
            )
            .order_by(InventoryLot.expiration_date)
        ).all()
        available = sum(lot.quantity for lot in lots)
        product = lots[0].product if lots else None
        if product is None or available < item.quantity:
            errors.append(f"Insufficient stock for product {item.product_id}.")
        elif classify(product, profile_data)[0] == RESTRICTED:
            errors.append(f"Product {item.product_id} is restricted.")
    return errors


def complete_checkout(database: Session, session: ShoppingSession, volunteer: User) -> Checkout:
    errors = validate_checkout(database, session)
    if errors:
        raise ValueError("; ".join(errors))
    completed_at = datetime.now(UTC)
    try:
        claim = database.execute(
            update(ShoppingSession)
            .where(ShoppingSession.id == session.id, ShoppingSession.status == "active")
            .values(status="completed", ended_at=completed_at)
        )
        if claim.rowcount != 1:
            raise ValueError("This shopping session was already checked out.")

        cart = database.scalar(select(Cart).where(Cart.session_id == session.id))
        checkout = Checkout(session_id=session.id, validated_by=volunteer.id, status="completed")
        database.add(checkout)
        database.flush()
        total_weight = 0.0
        for item in database.scalars(select(CartItem).where(CartItem.cart_id == cart.id)):
            lots = database.scalars(
                select(InventoryLot)
                .where(
                    InventoryLot.product_id == item.product_id,
                    InventoryLot.quantity > 0,
                    InventoryLot.expiration_date >= date.today(),
                )
                .order_by(InventoryLot.expiration_date, InventoryLot.received_at, InventoryLot.id)
            ).all()
            remaining = item.quantity
            for lot in lots:
                taken = min(remaining, lot.quantity)
                decremented = database.execute(
                    update(InventoryLot)
                    .where(InventoryLot.id == lot.id, InventoryLot.quantity >= taken)
                    .values(quantity=InventoryLot.quantity - taken)
                )
                if decremented.rowcount != 1:
                    raise ValueError(f"Insufficient stock for product {item.product_id}.")
                database.add(
                    InventoryMovement(
                        lot_id=lot.id,
                        change=-taken,
                        reason="checkout",
                        ref_id=checkout.id,
                    )
                )
                database.add(
                    CheckoutItem(
                        checkout_id=checkout.id,
                        product_id=item.product_id,
                        lot_id=lot.id,
                        quantity=taken,
                        status_at_checkout="Approved",
                    )
                )
                total_weight += (lot.product.weight_lb or 0) * taken
                remaining -= taken
                if remaining == 0:
                    break
            if remaining:
                raise ValueError(f"Insufficient stock for product {item.product_id}.")
        checkout.total_lb = total_weight
        checkout.completed_at = completed_at
        session.status = "completed"
        session.ended_at = completed_at
        database.add(
            Visit(
                client_id=session.client_id,
                session_id=session.id,
                completed_at=completed_at,
                pounds_distributed=total_weight,
            )
        )
        queue.promote_waiting(database)
        database.commit()
        return checkout
    except Exception:
        database.rollback()
        raise
