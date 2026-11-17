from __future__ import annotations

import math
from datetime import date
from itertools import islice

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models import (
    Cart,
    CartItem,
    Checkout,
    CheckoutItem,
    Client,
    InventoryLot,
    SavedRecipe,
    ShoppingListItem,
    ShoppingSession,
)
from app.rules.classify import RESTRICTED, household_label
from app.services.cart import active_session
from app.services.nutrition import members_for

POPULAR_COUNT = 10  # fallback size when the client has no qualifying picks
CHILD_AGE = 12  # under this age counts as half a portion (design §5 #6)


def household_portions(members: list[dict[str, object]], household_size: int) -> int:
    if not members:
        return max(1, household_size)
    portions = sum(0.5 if (m["age"] is not None and m["age"] < CHILD_AGE) else 1 for m in members)
    return max(1, math.ceil(portions))


def _past_products(database: Session, client: Client) -> set[int]:
    return set(
        database.scalars(
            select(CheckoutItem.product_id)
            .join(Checkout, Checkout.id == CheckoutItem.checkout_id)
            .join(ShoppingSession, ShoppingSession.id == Checkout.session_id)
            .where(ShoppingSession.client_id == client.user_id, Checkout.status == "completed")
        )
    )


def _saved_recipe_products(database: Session, client: Client) -> set[int]:
    recipes = database.scalars(
        select(SavedRecipe.recipe).where(SavedRecipe.client_id == client.user_id)
    )
    return {
        ingredient["product_id"]
        for recipe in recipes
        for ingredient in recipe.get("ingredients", [])
        if isinstance(ingredient.get("product_id"), int)
    }


def _list_products(database: Session, client: Client) -> set[int]:
    return set(
        database.scalars(
            select(ShoppingListItem.product_id).where(
                ShoppingListItem.client_id == client.user_id,
                ShoppingListItem.product_id.is_not(None),
                ShoppingListItem.ticked.is_(False),
            )
        )
    )


def _cart_products(database: Session, client: Client) -> set[int]:
    session = active_session(database, client)
    if session is None:
        return set()
    return set(
        database.scalars(
            select(CartItem.product_id).join(Cart).where(Cart.session_id == session.id)
        )
    )


def _popularity(database: Session) -> dict[int, int]:
    """Total quantity taken per product over all completed checkouts (aggregate, no clients)."""
    rows = database.execute(
        select(CheckoutItem.product_id, func.sum(CheckoutItem.quantity))
        .join(Checkout, Checkout.id == CheckoutItem.checkout_id)
        .where(Checkout.status == "completed")
        .group_by(CheckoutItem.product_id)
    )
    return {product_id: int(total) for product_id, total in rows}


def build_recommendations(database: Session, client: Client) -> list[dict[str, object]]:
    """In-stock picks from the client's history, saved recipes and shopping list.

    Items already in the active cart are hidden. With no qualifying pick, the warehouse's most
    taken products are shown instead.
    """
    members = members_for(client)
    quantity = household_portions(members, client.Household_Size)
    reasons_for = {
        "You took this on a past visit.": _past_products(database, client),
        "It's in a recipe you saved.": _saved_recipe_products(database, client),
        "It's on your shopping list.": _list_products(database, client),
    }
    in_cart = _cart_products(database, client)
    lots = database.scalars(
        select(InventoryLot)
        .options(joinedload(InventoryLot.product))
        .where(InventoryLot.quantity > 0, InventoryLot.expiration_date >= date.today())
        .order_by(InventoryLot.expiration_date, InventoryLot.id)
    ).all()
    first_lot: dict[int, InventoryLot] = {}
    for lot in lots:
        first_lot.setdefault(lot.product_id, lot)  # oldest stock per product

    def pick(lot: InventoryLot, extra_reasons: list[str]) -> dict[str, object] | None:
        label = household_label(lot.product, members)
        if label["status"] == RESTRICTED or label["allergy_match"]:  # never suggest an allergen
            return None
        return {
            "product_id": lot.product.id,
            "name": lot.product.name,
            "quantity": quantity,
            "status": label["status"],
            "rationale": " ".join([label["explanation"], *extra_reasons]),
            "not_for": label["not_for"],
            "allergy_match": label["allergy_match"],
            "aisle": lot.aisle,
            "shelf": lot.shelf,
            "bin": lot.bin,
        }

    available = {pid: lot for pid, lot in first_lot.items() if pid not in in_cart}
    picks = [
        pick(lot, [text for text, ids in reasons_for.items() if pid in ids])
        for pid, lot in available.items()
        if any(pid in ids for ids in reasons_for.values())
    ]
    picks = [p for p in picks if p]
    if picks:
        return picks

    taken = _popularity(database)
    ranked = sorted(available.items(), key=lambda entry: -taken.get(entry[0], 0))  # stable
    fallback = (
        pick(lot, ["Popular at the warehouse."] if pid in taken else []) for pid, lot in ranked
    )
    return list(islice(filter(None, fallback), POPULAR_COUNT))
