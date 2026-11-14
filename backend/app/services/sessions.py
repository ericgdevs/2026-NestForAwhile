import secrets

from fastapi import HTTPException
from sqlmodel import Session, select

from app.models import QueueStatus, SessionStatus, ShoppingSession, utcnow
from app.services import queue, recommendations


def active_session(session: Session, client_id: int) -> ShoppingSession | None:
    return session.exec(select(ShoppingSession).where(
        ShoppingSession.client_id == client_id, ShoppingSession.status == SessionStatus.ACTIVE)).first()


def start_session(session: Session, client_id: int) -> ShoppingSession:
    shopping = ShoppingSession(Shopping_Session_Token=secrets.token_urlsafe(32), client_id=client_id)
    session.add(shopping)
    session.commit()
    recommendations.generate_for_session(session, client_id, shopping.id)
    return shopping


def end_session(session: Session, client_id: int) -> None:
    shopping = active_session(session, client_id)
    if shopping:
        shopping.status = SessionStatus.COMPLETED
        shopping.ended_at = utcnow()
        session.add(shopping)
    queue.cancel_entries(session, client_id)
    session.commit()
    queue.refresh_queue(session)


def claim_turn(session: Session, client_id: int) -> ShoppingSession:
    queue.refresh_queue(session)
    entry = queue.current_entry(session, client_id)
    if entry is None:
        raise HTTPException(409, "Your spot expired. Please sign in again to rejoin the line.")
    if entry.status != QueueStatus.READY:
        raise HTTPException(409, "It isn't your turn yet.")
    shopping = start_session(session, client_id)
    entry.status = QueueStatus.CLAIMED
    entry.claimed_session_id = shopping.id
    session.add(entry)
    session.commit()
    return shopping
