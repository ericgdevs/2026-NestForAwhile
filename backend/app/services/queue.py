from datetime import datetime, timedelta, timezone

from sqlmodel import Session, select

from app.models import QueueEntry, QueueStatus, utcnow
from app.schemas import QueueState
from app.services import capacity

OPEN_STATUSES = (QueueStatus.WAITING, QueueStatus.READY)


def _aware(moment: datetime) -> datetime:
    return moment if moment.tzinfo else moment.replace(tzinfo=timezone.utc)


def _waiting_fifo(session: Session) -> list[QueueEntry]:
    return list(session.exec(
        select(QueueEntry).where(QueueEntry.status == QueueStatus.WAITING).order_by(QueueEntry.joined_at, QueueEntry.id)))


def refresh_queue(session: Session) -> None:
    """Expire unclaimed ready spots, then promote the oldest waiting clients while the floor has room."""
    window = timedelta(minutes=capacity.get_settings(session).claim_window_minutes)
    now = utcnow()
    for entry in session.exec(select(QueueEntry).where(QueueEntry.status == QueueStatus.READY)):
        if entry.ready_at and _aware(entry.ready_at) + window < now:
            entry.status = QueueStatus.EXPIRED
            session.add(entry)
    session.flush()
    for entry in _waiting_fifo(session):
        if not capacity.has_room(session):
            break
        entry.status = QueueStatus.READY
        entry.ready_at = now
        session.add(entry)
        session.flush()
    session.commit()


def current_entry(session: Session, client_id: int) -> QueueEntry | None:
    return session.exec(select(QueueEntry).where(
        QueueEntry.client_id == client_id, QueueEntry.status.in_(OPEN_STATUSES))).first()


def join_queue(session: Session, client_id: int) -> QueueEntry:
    entry = current_entry(session, client_id)
    if entry is None:
        entry = QueueEntry(client_id=client_id)
        session.add(entry)
        session.commit()
    return entry


def cancel_entries(session: Session, client_id: int) -> None:
    entry = current_entry(session, client_id)
    if entry:
        entry.status = QueueStatus.CANCELLED
        session.add(entry)
        session.commit()


def queue_state(session: Session, client_id: int) -> QueueState | None:
    entry = current_entry(session, client_id)
    if entry is None:
        return None
    if entry.status == QueueStatus.READY:
        return QueueState(status=entry.status, message="It's your turn. Please confirm you're here.")
    position = [e.id for e in _waiting_fifo(session)].index(entry.id) + 1
    return QueueState(status=entry.status, position=position,
                      message=f"The store is full right now. You are number {position} in line.")
