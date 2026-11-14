from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import InventoryLot


def product_location(database: Session, product_id: int) -> dict[str, str] | None:
    lot = database.scalar(
        select(InventoryLot)
        .where(InventoryLot.product_id == product_id, InventoryLot.quantity > 0)
        .order_by(InventoryLot.expiration_date)
    )
    if lot is None:
        return None
    return {"aisle": lot.aisle, "shelf": lot.shelf, "bin": lot.bin}


def available_product_ids(database: Session) -> set[int]:
    return set(
        database.scalars(
            select(InventoryLot.product_id).where(InventoryLot.quantity > 0)
        ).all()
    )
