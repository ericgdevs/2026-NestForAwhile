"""Match free-text list lines to in-stock products and build the shopping list view."""

from __future__ import annotations

import re
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import InventoryLot, Product, ShoppingListItem
from app.rules.classify import household_label

FILLER = {
    "a",
    "an",
    "of",
    "the",
    "and",
    "can",
    "cans",
    "bag",
    "bags",
    "box",
    "boxes",
    "jar",
    "jars",
    "lb",
    "lbs",
    "oz",
    "pack",
    "packs",
    "bottle",
    "bottles",
    "some",
    "x",
    "synthetic",
}


def split_lines(text: str) -> list[str]:
    parts = re.split(r"[\n,;]+", text)
    cleaned = [re.sub(r"^[\s\-*•\d.)x]+", "", part).strip() for part in parts]
    return [line[:120] for line in cleaned if line][:50]


def _words(text: str) -> set[str]:
    words = {word.rstrip("s") for word in re.findall(r"[a-z]+", text.lower())}
    return {word for word in words if word and word not in FILLER}


def first_lots(database: Session) -> dict[int, InventoryLot]:
    """Oldest in-stock lot per product: where to send the client."""
    lots = database.scalars(
        select(InventoryLot)
        .options(joinedload(InventoryLot.product))
        .where(InventoryLot.quantity > 0, InventoryLot.expiration_date >= date.today())
        .order_by(InventoryLot.expiration_date, InventoryLot.id)
    ).all()
    result: dict[int, InventoryLot] = {}
    for lot in lots:
        result.setdefault(lot.product_id, lot)
    return result


def location_of(lot: InventoryLot | None) -> dict[str, str] | None:
    return {"aisle": lot.aisle, "shelf": lot.shelf, "bin": lot.bin} if lot else None


def match_line(line: str, stocked: dict[int, InventoryLot]) -> Product | None:
    """Best in-stock product sharing at least half of the line's meaningful words."""
    wanted = _words(line)
    if not wanted:
        return None
    best, best_score = None, 0.0
    for lot in stocked.values():
        product = lot.product
        score = len(wanted & _words(f"{product.name} {product.category}")) / len(wanted)
        if score > best_score:
            best, best_score = product, score
    return best if best_score >= 0.5 else None


def item_view(
    item: ShoppingListItem,
    stocked: dict[int, InventoryLot],
    members: list[dict[str, object]],
) -> dict[str, object]:
    lot = stocked.get(item.product_id) if item.product_id else None
    view: dict[str, object] = {
        "id": item.id,
        "text": item.text,
        "product_id": item.product_id,
        "name": item.product.name if item.product else item.text,
        "source": item.source,
        "recipe": item.recipe,
        "ticked": item.ticked,
        "in_stock": lot is not None,
        "location": location_of(lot),
    }
    if item.product is not None:
        label = household_label(item.product, members)
        view.update(status=label["status"], not_for=label["not_for"])
    return view


def aisle_order(view: dict[str, object]) -> tuple:
    location = view["location"] or {}
    return (
        view["location"] is None,
        location.get("aisle", ""),
        location.get("shelf", ""),
        location.get("bin", ""),
        view["id"],
    )
