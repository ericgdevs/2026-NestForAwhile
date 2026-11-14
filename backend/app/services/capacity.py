from sqlmodel import Session, func, select

from app.models import CapacitySettings, QueueEntry, QueueStatus, SessionStatus, ShoppingSession, utcnow
from app.schemas import CapacityResponse

DEFAULT_MAX_FLOOR_CAPACITY = 20


def get_settings(session: Session) -> CapacitySettings:
    settings = session.get(CapacitySettings, 1)
    if settings is None:
        settings = CapacitySettings(Max_Floor_Capacity=DEFAULT_MAX_FLOOR_CAPACITY)
        session.add(settings)
        session.commit()
    return settings


def _count(session: Session, model, *conditions) -> int:
    return session.exec(select(func.count()).select_from(model).where(*conditions)).one()


def active_floor_shoppers(session: Session) -> int:
    """Shoppers on the floor plus queue entries holding a ready spot. Computed, never stored."""
    active = _count(session, ShoppingSession, ShoppingSession.status == SessionStatus.ACTIVE)
    return active + _count(session, QueueEntry, QueueEntry.status == QueueStatus.READY)


def queue_waiting(session: Session) -> int:
    return _count(session, QueueEntry, QueueEntry.status == QueueStatus.WAITING)


def has_room(session: Session) -> bool:
    return active_floor_shoppers(session) < get_settings(session).Max_Floor_Capacity


def get_capacity(session: Session) -> CapacityResponse:
    return CapacityResponse(
        Active_Floor_Shoppers=active_floor_shoppers(session),
        Max_Floor_Capacity=get_settings(session).Max_Floor_Capacity,
        Queue_Waiting=queue_waiting(session),
    )


def set_max_capacity(session: Session, value: int, user_id: int) -> CapacityResponse:
    settings = get_settings(session)
    settings.Max_Floor_Capacity = value
    settings.updated_by = user_id
    settings.updated_at = utcnow()
    session.add(settings)
    session.commit()
    return get_capacity(session)
