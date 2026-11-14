"""Where a client is in their visit, so the phone can show the right screen."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Checkout, Client, ShoppingSession
from app.services.cart import active_session
from app.services.queue import queue_state
from app.services.sessions import start_session

COMPLETE_SCREEN_HOURS = 12  # after this, a finished visit stops showing its "visit complete" screen


def _recent_checkout(database: Session, client: Client) -> dict[str, object] | None:
    since = datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=COMPLETE_SCREEN_HOURS)
    row = database.execute(
        select(Checkout, ShoppingSession)
        .join(ShoppingSession, ShoppingSession.id == Checkout.session_id)
        .where(
            ShoppingSession.client_id == client.user_id,
            Checkout.status == "completed",
            Checkout.completed_at >= since,
        )
        .order_by(Checkout.completed_at.desc())
    ).first()
    if row is None:
        return None
    checkout, _ = row
    return {
        "checkout_id": checkout.id,
        "total_lb": checkout.total_lb,
        "completed_at": checkout.completed_at.isoformat(),
    }


def visit_state(database: Session, client: Client) -> dict[str, object]:
    """awaiting_approval | inactive | shopping | queued | complete | none."""
    if client.Client_Enrollment_Status == "Pending":
        return {"status": "awaiting_approval"}
    if client.Client_Enrollment_Status != "Active":
        return {"status": "inactive"}
    session = active_session(database, client)
    if session is not None:
        return {"status": "shopping", "Shopping_Session_Token": session.Shopping_Session_Token}
    queue = queue_state(database, client.user_id)
    if queue["status"] in ("waiting", "ready"):
        return {
            "status": "queued",
            "queue_status": queue["status"],
            "position": queue["position"],
            "message": queue["message"],
        }
    receipt = _recent_checkout(database, client)
    if receipt is not None:
        return {"status": "complete", "receipt": receipt}
    return {"status": "none"}


def check_in(database: Session, client: Client) -> dict[str, object]:
    """Start a visit for an approved client (no password needed while signed in)."""
    state = visit_state(database, client)
    if state["status"] in ("none", "complete"):
        start_session(database, client)  # joins the queue instead when the floor is full
        state = visit_state(database, client)
    return state
