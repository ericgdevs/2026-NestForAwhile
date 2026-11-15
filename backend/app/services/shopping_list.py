"""Match free-text list lines to in-stock products and build the shopping list view."""

from __future__ import annotations

import re
from difflib import get_close_matches
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import Cart, CartItem, Client, InventoryLot, Product, ShoppingListItem, User
from app.rules.classify import RESTRICTED, household_label
from app.services.cart import active_session
from app.services.nutrition import members_for
from app.services.swaps import find_swaps

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
        have = _words(f"{product.name} {product.category}")
        # Close spellings count too ("blak bean"), so a handwritten typo still matches.
        score = sum(1 for w in wanted if w in have or get_close_matches(w, have, 1, 0.8)) / len(wanted)
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
        "recipes": recipes_of(item),
        "ticked": item.ticked,
        "in_stock": lot is not None,
        "location": location_of(lot),
    }
    if item.product is not None:
        label = household_label(item.product, members)
        view.update(status=label["status"], not_for=label["not_for"])
    return view


def recipes_of(item: ShoppingListItem) -> list[dict]:
    """The `recipe` column holds a list of recipes; rows saved before 2026-11-14 hold one dict."""
    if not item.recipe:
        return []
    return item.recipe if isinstance(item.recipe, list) else [item.recipe]


def find_same_line(
    items: list[ShoppingListItem], product_id: int | None, text: str
) -> ShoppingListItem | None:
    """One line per product (or per free-text item when nothing in stock matched)."""
    for item in items:
        if product_id is not None and item.product_id == product_id:
            return item
        if product_id is None and item.product_id is None and item.text.lower() == text.lower():
            return item
    return None


def merge_into_line(item: ShoppingListItem, recipe: dict | None) -> None:
    """Tag the line with this recipe too, or mark it as the client's own item."""
    recipes = recipes_of(item)
    if recipe is None:
        item.source = "you"
    elif all(existing.get("title") != recipe.get("title") for existing in recipes):
        recipes = [*recipes, recipe]
    item.recipe = recipes  # reassign so SQLAlchemy saves the JSON change


def aisle_order(view: dict[str, object]) -> tuple:
    location = view["location"] or {}
    return (
        view["location"] is None,
        location.get("aisle", ""),
        location.get("shelf", ""),
        location.get("bin", ""),
        view["id"],
    )


NOT_STOCKED = " — not stocked today"


def note_text(name: str) -> str:
    """Plain-note wording for an item we can't point the client to."""
    return name[: 120 - len(NOT_STOCKED)] + NOT_STOCKED


def cart_product_ids(database: Session, client: Client) -> set[int]:
    session = active_session(database, client)
    if session is None:
        return set()
    return set(
        database.scalars(
            select(CartItem.product_id).join(Cart).where(Cart.session_id == session.id)
        )
    )


def add_recipe_to_list(
    database: Session, user: User, recipe: dict, skip_product_id: int | None = None
) -> dict[str, object]:
    """Put a recipe's missing ingredients on the list; never ones in the cart, already listed,
    or restricted for the household (those come back with the reason and in-stock swaps)."""
    client = database.get(Client, user.id)
    members = members_for(client)
    stocked = first_lots(database)
    in_cart = cart_product_ids(database, client)
    existing = list(
        database.scalars(select(ShoppingListItem).where(ShoppingListItem.client_id == user.id))
    )
    added, blocked, seen = [], [], set()
    counts = {"in_cart": 0, "already_on_list": 0}
    for ingredient in recipe["ingredients"]:
        product_id, name = ingredient.get("product_id"), ingredient["name"]
        if product_id == skip_product_id and product_id is not None:
            continue
        if (product_id, name) in seen:
            continue
        seen.add((product_id, name))
        product = database.get(Product, product_id) if product_id is not None else None
        if product is not None and product.id in in_cart:
            counts["in_cart"] += 1
            continue
        label = household_label(product, members) if product is not None else None
        # "Restricted for anyone": the label is Red only when everyone is blocked, so check not_for.
        if label and (label["status"] == RESTRICTED or label["not_for"]):
            blocked.append(
                {
                    "name": name,
                    "not_for": label["not_for"],
                    "swaps": find_swaps(database, product, members),
                }
            )
            continue
        in_stock = product is not None and product.id in stocked
        # Not carried or out of stock: a plain note, never a product row with a safety colour.
        text, line_product = (name, product.id) if in_stock else (note_text(name), None)
        if product is None:
            text = name  # a pantry item the catalog doesn't know stays as the recipe wrote it
        item = find_same_line(existing, line_product, text)
        if item is not None:
            counts["already_on_list"] += 1
        else:
            item = ShoppingListItem(client_id=user.id, product_id=line_product, text=text)
            item.source, item.recipe = "recipe", []
            database.add(item)
            existing.append(item)
            added.append(
                {
                    "name": product.name if in_stock else text,
                    "location": location_of(stocked.get(product.id)) if in_stock else None,
                }
            )
        merge_into_line(item, recipe)
    database.commit()
    return {"added": added, "blocked": blocked, **counts}
