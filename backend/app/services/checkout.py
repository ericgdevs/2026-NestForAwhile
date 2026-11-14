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
    Intervention,
    InventoryLot,
    InventoryMovement,
    Product,
    ShoppingSession,
    User,
    Visit,
)
from app.rules.classify import RESTRICTED, household_label
from app.services import queue
from app.services.nutrition import members_for


def session_by_token(database: Session, token: str) -> ShoppingSession | None:
    return database.scalar(
        select(ShoppingSession).where(
            ShoppingSession.Shopping_Session_Token == token,
            ShoppingSession.status == "active",
        )
    )


ALLERGY_ACK = "allergy_ack"
MANAGER_OVERRIDE = "manager_override"


def _cart_items(database: Session, session: ShoppingSession) -> list[CartItem]:
    cart = database.scalar(select(Cart).where(Cart.session_id == session.id))
    if cart is None:
        return []
    return list(database.scalars(select(CartItem).where(CartItem.cart_id == cart.id)))


def _logged(database: Session, session: ShoppingSession, action: str) -> set[int]:
    """Product IDs with a recorded intervention of this kind for the session."""
    return set(
        database.scalars(
            select(Intervention.product_id)
            .join(Checkout, Checkout.id == Intervention.checkout_id)
            .where(Checkout.session_id == session.id, Intervention.action == action)
        )
    )


def record_intervention(
    database: Session,
    session: ShoppingSession,
    user: User,
    product_id: int,
    action: str,
    note: str | None = None,
) -> Intervention:
    """Log a volunteer/manager action against the session's review checkout row."""
    review = database.scalar(
        select(Checkout).where(Checkout.session_id == session.id, Checkout.status == "blocked")
    )
    if review is None:
        review = Checkout(session_id=session.id, validated_by=user.id, status="blocked")
        database.add(review)
        database.flush()
    entry = Intervention(
        checkout_id=review.id,
        product_id=product_id,
        volunteer_id=user.id,
        action=action,
        note=note,
    )
    database.add(entry)
    return entry


def review_checkout(database: Session, session: ShoppingSession) -> dict[str, object]:
    """Everything the volunteer must see: labelled items, hard stops, and allergy confirmations."""
    client = database.get(Client, session.client_id)
    members = members_for(client)
    acknowledged = _logged(database, session, ALLERGY_ACK)
    overridden = _logged(database, session, MANAGER_OVERRIDE)
    items, blocking, needs_ack = [], [], []
    cart_items = _cart_items(database, session)
    if not cart_items:
        blocking.append("Cart is empty.")
    if client is not None and client.Client_Enrollment_Status != "Active":
        blocking.append("This account is waiting for staff approval.")
    for item in cart_items:
        product = database.get(Product, item.product_id)
        available = sum(
            database.scalars(
                select(InventoryLot.quantity).where(
                    InventoryLot.product_id == item.product_id,
                    InventoryLot.quantity > 0,
                    InventoryLot.expiration_date >= date.today(),
                )
            )
        )
        label = household_label(product, members)
        if available < item.quantity:
            blocking.append(f"Insufficient stock for product {item.product_id}.")
        if label["status"] == RESTRICTED and item.product_id not in overridden:
            blocking.append(
                f"{product.name} isn't safe for anyone in this household. "
                "Remove it, or a manager can record an override."
            )
        if label["allergy_match"] and item.product_id not in acknowledged:
            needs_ack.append(
                {"product_id": item.product_id, "name": product.name, "not_for": label["not_for"]}
            )
        items.append(
            {
                "product_id": item.product_id,
                "name": product.name,
                "quantity": item.quantity,
                "status": label["status"],
                "not_for": label["not_for"],
                "allergy_match": label["allergy_match"],
                "acknowledged": item.product_id in acknowledged,
                "overridden": item.product_id in overridden,
            }
        )
    return {
        "Shopping_Session_Token": session.Shopping_Session_Token,
        "client_id": session.client_id,
        "Client_Enrollment_Status": client.Client_Enrollment_Status if client else None,
        "items": items,
        "blocking": blocking,
        "needs_ack": needs_ack,
    }


def validate_checkout(database: Session, session: ShoppingSession) -> list[str]:
    """Hard stops plus any allergy still waiting for the volunteer to confirm with the client."""
    review = review_checkout(database, session)
    unconfirmed = [
        f"Confirm with the client: {entry['name']} is not for "
        + ", ".join(f"{who['nickname']} ({who['reason']})" for who in entry["not_for"])
        + "."
        for entry in review["needs_ack"]
    ]
    return [*review["blocking"], *unconfirmed]


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
