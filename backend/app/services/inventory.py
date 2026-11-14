from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AuditEvent, InventoryLot, InventoryMovement, Product


def product_lots(database: Session, product_id: int) -> list[InventoryLot]:
    return list(
        database.scalars(
            select(InventoryLot)
            .where(InventoryLot.product_id == product_id, InventoryLot.quantity >= 0)
            .order_by(InventoryLot.expiration_date, InventoryLot.received_at, InventoryLot.id)
        )
    )


def audit_product(database: Session, product_id: int, counted_qty: int, counted_by: int) -> dict:
    if counted_qty < 0:
        raise ValueError("counted_qty must be non-negative")
    lots = product_lots(database, product_id)
    if not lots:
        raise LookupError("Product inventory not found")
    expected = sum(lot.quantity for lot in lots)
    variance = counted_qty - expected
    ordered = lots if variance < 0 else list(reversed(lots))
    if variance < 0:
        remaining_to_remove = -variance
        for lot in ordered:
            change = min(remaining_to_remove, lot.quantity)
            lot.quantity -= change
            remaining_to_remove -= change
            if change:
                database.add(
                    InventoryMovement(lot_id=lot.id, change=-change, reason="audit")
                )
            if remaining_to_remove == 0:
                break
    elif variance > 0:
        lot = ordered[0]
        lot.quantity += variance
        database.add(InventoryMovement(lot_id=lot.id, change=variance, reason="audit"))
    database.add(
        AuditEvent(
            product_id=product_id,
            lot_id=ordered[0].id,
            expected_qty=expected,
            counted_qty=counted_qty,
            variance=variance,
            counted_by=counted_by,
        )
    )
    database.commit()
    return {"expected_qty": expected, "counted_qty": counted_qty, "variance": variance}


def lot_rows(database: Session) -> list[dict]:
    today = date.today()
    cutoff = today + timedelta(days=7)
    rows = []
    for lot in database.scalars(
        select(InventoryLot)
        .where(InventoryLot.expiration_date >= today)
        .order_by(InventoryLot.expiration_date, InventoryLot.received_at, InventoryLot.id)
    ):
        rows.append(
            {
                "lot_id": lot.id,
                "product_id": lot.product_id,
                "quantity": lot.quantity,
                "expiration_date": lot.expiration_date,
                "expiring_soon": lot.expiration_date <= cutoff,
            }
        )
    return rows


def replenishment_rows(database: Session, sort: str) -> list[dict]:
    rows = []
    for lot in database.scalars(
        select(InventoryLot)
        .join(Product)
        .where(InventoryLot.quantity < InventoryLot.reorder_threshold)
    ):
        ratio = lot.quantity / lot.reorder_threshold if lot.reorder_threshold else 0
        rows.append(
            {
                "product_id": lot.product_id,
                "name": lot.product.name,
                "quantity": lot.quantity,
                "reorder_threshold": lot.reorder_threshold,
                "aisle": lot.aisle,
                "shelf": lot.shelf,
                "bin": lot.bin,
                "priority": round(ratio * 100),
            }
        )
    if sort == "location":
        rows.sort(key=lambda row: (row["aisle"], row["shelf"], row["bin"]))
    elif sort == "name":
        rows.sort(key=lambda row: row["name"])
    else:
        rows.sort(key=lambda row: (row["priority"], row["name"]))
    return rows
