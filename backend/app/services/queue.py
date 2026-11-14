from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import CapacitySetting, Client, QueueEntry, ShoppingSession


def _capacity(database: Session) -> CapacitySetting:
    setting = database.scalar(select(CapacitySetting).order_by(CapacitySetting.id))
    if setting is None:
        setting = CapacitySetting(Max_Floor_Capacity=10, claim_window_minutes=5)
        database.add(setting)
        database.flush()
    return setting


def active_count(database: Session) -> int:
    return (
        database.scalar(
            select(func.count(ShoppingSession.id)).where(ShoppingSession.status == "active")
        )
        or 0
    ) + (
        database.scalar(select(func.count(QueueEntry.id)).where(QueueEntry.status == "ready"))
        or 0
    )


def promote_waiting(database: Session) -> None:
    setting = _capacity(database)
    while active_count(database) < setting.Max_Floor_Capacity:
        entry = database.scalar(
            select(QueueEntry)
            .where(QueueEntry.status == "waiting")
            .order_by(QueueEntry.joined_at, QueueEntry.id)
        )
        if entry is None:
            break
        entry.status = "ready"
        entry.ready_at = datetime.now(UTC)


def queue_state(database: Session, client_id: int) -> dict:
    now = datetime.now(UTC)
    for entry in database.scalars(
        select(QueueEntry).where(QueueEntry.client_id == client_id).order_by(QueueEntry.id.desc())
    ):
        if entry.status == "ready" and entry.ready_at:
            setting = _capacity(database)
            if now > entry.ready_at + timedelta(minutes=setting.claim_window_minutes):
                entry.status = "expired"
                entry.ready_at = None
                promote_waiting(database)
                continue
        if entry.status in {"waiting", "ready"}:
            position = None
            if entry.status == "waiting":
                position = (
                    database.scalar(
                        select(func.count(QueueEntry.id)).where(
                            QueueEntry.status == "waiting",
                            QueueEntry.joined_at <= entry.joined_at,
                        )
                    )
                    or 1
                )
            return {
                "status": entry.status,
                "position": position,
                "message": (
                    "Your turn is ready." if entry.status == "ready" else "You are in the queue."
                ),
            }
    return {"status": "cancelled", "position": None, "message": "No active queue entry."}


def enqueue(database: Session, client: Client) -> None:
    existing = database.scalar(
        select(QueueEntry).where(
            QueueEntry.client_id == client.user_id,
            QueueEntry.status.in_(("waiting", "ready")),
        )
    )
    if existing is None:
        database.add(QueueEntry(client_id=client.user_id, status="waiting"))
    database.commit()


def claim_ready(database: Session, client: Client) -> str:
    state = queue_state(database, client.user_id)
    if state["status"] != "ready":
        raise ValueError("Your queue turn is not ready")
    entry = database.scalar(
        select(QueueEntry)
        .where(QueueEntry.client_id == client.user_id, QueueEntry.status == "ready")
        .order_by(QueueEntry.id.desc())
    )
    if entry is None:
        raise ValueError("Your queue turn is not ready")
    entry.status = "claimed"
    token = secrets.token_urlsafe(32)
    session = ShoppingSession(
        Shopping_Session_Token=token,
        client_id=client.user_id,
        status="active",
    )
    database.add(session)
    database.flush()
    entry.claimed_session_id = session.id
    database.commit()
    return token


def end_client_session(database: Session, client_id: int) -> None:
    session = database.scalar(
        select(ShoppingSession).where(
            ShoppingSession.client_id == client_id,
            ShoppingSession.status == "active",
        )
    )
    if session:
        session.status = "cancelled"
        session.ended_at = datetime.now(UTC)
        promote_waiting(database)
        database.commit()
