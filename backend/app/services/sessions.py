import secrets

from fastapi import HTTPException
from sqlmodel import Session, select

from app.models import ClientProfile, EnrollmentStatus, QueueStatus, Role, SessionStatus, ShoppingSession, User, utcnow
from app.schemas import LoginResult
from app.services import capacity, queue, recommendations


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


def initialize(session: Session, user: User) -> LoginResult:
    """Initialize Shopping Session: enrollment check, capacity check, then start a session or join the queue."""
    if user.role != Role.CLIENT:
        return LoginResult(role=user.role)
    client = session.get(ClientProfile, user.id)
    if client is None or client.Client_Enrollment_Status != EnrollmentStatus.ACTIVE:
        raise HTTPException(403, "Your enrollment isn't active yet. Please ask a volunteer for help.")
    existing = active_session(session, user.id)
    if existing:
        return LoginResult(role=user.role, Shopping_Session_Token=existing.Shopping_Session_Token)
    queue.refresh_queue(session)
    if queue.current_entry(session, user.id) is None:
        # shortcut: no row lock, two simultaneous logins on PostgreSQL could overfill by one; add SELECT FOR UPDATE on capacity_settings when load matters
        if capacity.has_room(session) and capacity.queue_waiting(session) == 0:
            shopping = start_session(session, user.id)
            return LoginResult(role=user.role, Shopping_Session_Token=shopping.Shopping_Session_Token)
        queue.join_queue(session, user.id)
    return LoginResult(role=user.role, queue=queue.queue_state(session, user.id))
