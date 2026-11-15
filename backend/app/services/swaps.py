"""Safer in-stock swaps for a Red product, chosen by rules and inventory (never AI)."""

from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import InventoryLot, Product
from app.rules.classify import APPROVED, CAPPED, household_label

MAX_SWAPS = 2


def find_swaps(
    database: Session,
    product: Product,
    members: list[dict[str, object]],
    limit: int = MAX_SWAPS,
) -> list[dict[str, object]]:
    """Same category, in stock, Green first then Yellow; one entry per product with its location.

    `product` only needs `.id` and `.category`; a None category searches every category.
    """
    lots = database.scalars(
        select(InventoryLot)
        .options(joinedload(InventoryLot.product))
        .join(Product)
        .where(
            *([Product.category == product.category] if product.category else []),
            Product.id != product.id,
            InventoryLot.quantity > 0,
            InventoryLot.expiration_date >= date.today(),
        )
        .order_by(InventoryLot.expiration_date, InventoryLot.id)  # oldest stock first
    ).all()
    first_lot: dict[int, InventoryLot] = {}
    for lot in lots:
        first_lot.setdefault(lot.product_id, lot)

    ranked = []
    for lot in first_lot.values():
        label = household_label(lot.product, members)
        if label["status"] in (APPROVED, CAPPED):
            ranked.append((label["status"] != APPROVED, lot, label))
    ranked.sort(key=lambda entry: entry[0])
    return [
        {
            "product_id": lot.product.id,
            "name": lot.product.name,
            "status": label["status"],
            "not_for": label["not_for"],
            "aisle": lot.aisle,
            "shelf": lot.shelf,
            "bin": lot.bin,
        }
        for _, lot, label in ranked[:limit]
    ]
