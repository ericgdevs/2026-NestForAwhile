from sqlmodel import Session

from app.models import InventoryMovement


def log_movement(session: Session, lot_id: int, change: int, reason: str, ref_id: int | None = None) -> InventoryMovement:
    """Stage a movement row; the caller commits so it lands in the same transaction as the stock change."""
    movement = InventoryMovement(lot_id=lot_id, change=change, reason=reason, ref_id=ref_id)
    session.add(movement)
    return movement
