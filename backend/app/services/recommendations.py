from __future__ import annotations

import math
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import Checkout, CheckoutItem, Client, InventoryLot, SavedRecipe, ShoppingSession
from app.rules.classify import RESTRICTED, household_label
from app.services.nutrition import members_for

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


def build_recommendations(database: Session, client: Client) -> list[dict[str, object]]:
    """In-stock picks sized to the household; past visits and saved recipes come first."""
    members = members_for(client)
    quantity = household_portions(members, client.Household_Size)
    taken_before = _past_products(database, client)
    in_saved = _saved_recipe_products(database, client)
    lots = database.scalars(
        select(InventoryLot)
        .options(joinedload(InventoryLot.product))
        .where(InventoryLot.quantity > 0, InventoryLot.expiration_date >= date.today())
        .order_by(InventoryLot.expiration_date, InventoryLot.id)
    ).all()
    recommendations = []
    seen_products: set[int] = set()
    for lot in lots:
        product = lot.product
        if product.id in seen_products:
            continue
        seen_products.add(product.id)
        label = household_label(product, members)
        if label["status"] == RESTRICTED:
            continue
        reasons = [label["explanation"]]
        if product.id in taken_before:
            reasons.append("You took this on a past visit.")
        if product.id in in_saved:
            reasons.append("It's in a recipe you saved.")
        recommendations.append(
            {
                "product_id": product.id,
                "name": product.name,
                "quantity": quantity,
                "status": label["status"],
                "rationale": " ".join(reasons),
                "not_for": label["not_for"],
                "allergy_match": label["allergy_match"],
                "aisle": lot.aisle,
                "shelf": lot.shelf,
                "bin": lot.bin,
                "_rank": (product.id not in taken_before and product.id not in in_saved),
            }
        )
    recommendations.sort(key=lambda pick: pick["_rank"])  # stable: keeps oldest-stock order
    return [{k: v for k, v in pick.items() if k != "_rank"} for pick in recommendations]
