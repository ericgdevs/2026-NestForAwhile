import re
from datetime import date

from sqlmodel import Session, select

from app.models import InventoryLocation, InventoryLot, Product
from app.schemas import ReplenishmentItem
from app.services import fifo


def _natural(text: str) -> list:
    """A2 sorts before A10, so walking the list follows the floor layout."""
    return [int(part) if part.isdigit() else part for part in re.split(r"(\d+)", text)]


def _location_key(item: ReplenishmentItem) -> tuple:
    return (_natural(item.aisle), _natural(item.shelf), _natural(item.bin), item.name)


def list_replenishment(
    session: Session, sort: str = "priority", today: date | None = None
) -> list[ReplenishmentItem]:
    """Products whose usable stock is below their reorder threshold.

    Priority 1 is the lowest stock-to-threshold ratio.
    """
    today = today or date.today()
    lots_by_product: dict[int, list[InventoryLot]] = {}
    for lot in session.exec(select(InventoryLot)).all():
        lots_by_product.setdefault(lot.product_id, []).append(lot)
    locations = {loc.id: loc for loc in session.exec(select(InventoryLocation))}
    products = {p.id: p for p in session.exec(select(Product))}

    needed = []
    for product_id, lots in lots_by_product.items():
        usable = sum(lot.quantity for lot in lots if not fifo.is_expired(lot, today))
        threshold = max(lot.reorder_threshold for lot in lots)
        if usable < threshold:
            where = next(
                (
                    locations[lot.location_id]
                    for lot in sorted(lots, key=fifo.fifo_key)
                    if lot.location_id
                ),
                None,
            )
            needed.append((usable / threshold, products[product_id], usable, threshold, where))

    needed.sort(key=lambda row: (row[0], row[1].name))
    items = [
        ReplenishmentItem(
            product_id=p.id,
            name=p.name,
            quantity=qty,
            reorder_threshold=threshold,
            aisle=where.aisle if where else "",
            shelf=where.shelf if where else "",
            bin=where.bin if where else "",
            priority=rank,
        )
        for rank, (_, p, qty, threshold, where) in enumerate(needed, start=1)
    ]
    if sort == "location":
        items.sort(key=_location_key)
    elif sort == "name":
        items.sort(key=lambda item: item.name)
    return items
