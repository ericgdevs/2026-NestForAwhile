from datetime import date

from sqlmodel import Session, select

from app.models import InventoryLot

EXPIRING_SOON_DAYS = 7


def fifo_key(lot: InventoryLot) -> tuple:
    """Consume earliest-expiring stock first, then receipt time and id for stable ties."""
    return (lot.expiration_date or date.max, lot.received_at, lot.id)


def is_expired(lot: InventoryLot, today: date) -> bool:
    return lot.expiration_date is not None and lot.expiration_date < today


def is_expiring_soon(lot: InventoryLot, today: date) -> bool:
    """0 to 7 days left, inclusive; day 8 is not flagged and expired lots are not 'soon'."""
    if lot.expiration_date is None:
        return False
    return 0 <= (lot.expiration_date - today).days <= EXPIRING_SOON_DAYS


def all_lots_fifo(session: Session) -> list[InventoryLot]:
    lots = session.exec(select(InventoryLot).where(InventoryLot.quantity > 0)).all()
    return sorted(lots, key=fifo_key)


def usable_lots_fifo(
    session: Session, product_id: int, today: date | None = None
) -> list[InventoryLot]:
    """In-stock, non-expired lots of one product in the order checkout must take them."""
    today = today or date.today()
    lots = session.exec(select(InventoryLot).where(InventoryLot.product_id == product_id,
                                                   InventoryLot.quantity > 0)).all()
    return sorted((lot for lot in lots if not is_expired(lot, today)), key=fifo_key)
