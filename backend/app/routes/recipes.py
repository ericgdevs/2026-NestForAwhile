from __future__ import annotations

import logging
import time

from fastapi import APIRouter, Body, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.context_manifest import build_manifest as build_ai_manifest
from app.ai.fallback import build_fallback_recipes
from app.ai.orchestrator import AIOrchestrationError, run_ai_task
from app.ai.provider import AITask
from app.ai.rules_guard import apply_rules_guard
from app.auth import Role, require_roles
from app.db import get_db
from app.models import AIRequest, Client, InventoryLot, Product, User
from app.rules.classify import APPROVED, RESTRICTED, classify
from app.services.cart import active_session, build_manifest, get_or_create_cart
from app.services.nutrition import household_choices
from app.services.recipe_guard import guard_recipes

router = APIRouter()
logger = logging.getLogger(__name__)
MANIFEST_EXTRAS = 25  # in-stock products sent to the AI besides the scanned item and cart


def _allowed_stock(database: Session, profile_data: dict):
    """In-stock products the rules allow (never Restricted) with their first-expiring location."""
    lots = database.scalars(
        select(InventoryLot)
        .where(InventoryLot.quantity > 0)
        .order_by(InventoryLot.expiration_date, InventoryLot.id)
    ).all()
    locations = {}
    for lot in lots:
        location = {"aisle": lot.aisle, "shelf": lot.shelf, "bin": lot.bin}
        locations.setdefault(lot.product_id, location)
    candidates = database.scalars(
        select(Product).where(Product.id.in_(locations)).order_by(Product.id)
    )
    return {p.id: p for p in candidates if classify(p, profile_data)[0] != RESTRICTED}, locations


def manifest_products(products: dict, cart: list[dict], profile_data: dict, focus_id: int | None):
    """Scanned item + cart items + up to MANIFEST_EXTRAS others, so the request stays small.

    Others are picked round-robin across categories, the scanned item's category first and
    Approved before Capped, so recipes still get a varied, closest-fitting shortlist.
    """
    must = list(
        dict.fromkeys(i for i in (focus_id, *(r["product_id"] for r in cart)) if i in products)
    )
    focus = products.get(focus_id)
    groups: dict[str, list] = {}
    for product in products.values():
        if product.id not in must:
            groups.setdefault(product.category, []).append(product)
    for group in groups.values():
        group.sort(key=lambda p: classify(p, profile_data)[0] != APPROVED)  # stable
    order = sorted(groups, key=lambda c: (not focus or c != focus.category, c))
    picked: list = []
    while len(picked) < MANIFEST_EXTRAS and any(groups.values()):
        for category in order:
            if groups[category] and len(picked) < MANIFEST_EXTRAS:
                picked.append(groups[category].pop(0))
    return [products[i] for i in must] + picked


class RecipeRequest(BaseModel):
    scanned_product_id: int | None = None
    cuisine: str | None = Field(default=None, max_length=30)


def _matches(recipe: dict, focus: int | None, cuisine: str | None) -> bool:
    uses_focus = focus is None or any(i["product_id"] == focus for i in recipe["ingredients"])
    same_cuisine = cuisine is None or (recipe.get("cuisine") or "").lower() == cuisine.lower()
    return uses_focus and same_cuisine


def _with_locations(recipes: list[dict], locations: dict, stocked: set[int]) -> list[dict]:
    """Fill the contract's per-ingredient location and in-stock flag."""
    return [
        {
            **recipe,
            "ingredients": [
                {
                    **ingredient,
                    "in_cart_or_stock": ingredient["product_id"] in stocked,
                    "location": locations.get(ingredient["product_id"]),
                }
                for ingredient in recipe["ingredients"]
            ],
        }
        for recipe in recipes
    ]


def _ai_suggestions(
    products, locations, cart, profile_data, household_size, focus=None, cuisine=None
):
    """Guarded recipes from one AI call; raises if the AI cannot give a safe recipe.

    The old second "missing ingredients" call had no instructions and no "JSON" in its prompt, so
    Groq answered 400 after every 200. It was optional and swallowed, so it is gone.
    """
    items = manifest_products(products, cart, profile_data, focus)
    restrictions = [*profile_data["restrictions"], *profile_data["allergies"]]
    quantities = {row["product_id"]: row["quantity"] for row in cart}
    manifest, index_map = build_ai_manifest(items, restrictions, quantities, household_size)
    in_stock = set(products)

    result = run_ai_task(
        AITask.RECIPES,
        items,
        restrictions,
        quantities,
        household_size,
        focus_product_id=focus,
        cuisine=cuisine,
    )
    output = apply_rules_guard(result, manifest, items, restrictions, in_stock).output
    recipes = guard_recipes(
        [
            {
                "title": recipe.title,
                "cuisine": recipe.cuisine,
                "steps": recipe.steps,
                "ingredients": [
                    {"name": i.name, "product_id": index_map.get(i.product_id)}
                    for i in recipe.ingredients
                ],
            }
            for recipe in output.recipes
        ],
        products,
        profile_data,
        in_stock,
    )
    recipes = [recipe for recipe in recipes if _matches(recipe, focus, cuisine)]
    if not recipes:
        raise AIOrchestrationError("no safe recipes")
    return result.provider, recipes, []


@router.post("/recipes")
def recipes(
    payload_in: RecipeRequest | None = Body(default=None),
    current_user: User = Depends(require_roles(Role.CLIENT)),
    database: Session = Depends(get_db),
):
    request = payload_in or RecipeRequest()
    started = time.monotonic()
    client = database.get(Client, current_user.id)
    session = active_session(database, client) if client else None
    cart = get_or_create_cart(database, session) if session else None
    manifest = build_manifest(database, cart) if cart else []
    profile_data = household_choices(client)  # stricter than the label: safe for every member
    try:
        products, locations = _allowed_stock(database, profile_data)
    except ValueError:
        products, locations = {}, {}  # unclassifiable profile: fail closed
    provider, payload, missing = "fallback", None, []
    try:
        provider, payload, missing = _ai_suggestions(
            products,
            locations,
            manifest,
            profile_data,
            client.Household_Size if client else None,
            request.scanned_product_id,
            request.cuisine,
        )
    except Exception as exc:  # any AI failure falls through to the deterministic fallback
        cause = exc.__cause__ or exc
        status = getattr(cause, "status_code", None)  # type and status only: no prompt, no PHI
        logger.warning("Recipe AI fell back: %s status=%s", type(cause).__name__, status)
    used_fallback = payload is None
    if used_fallback:
        inventory = [{"product_id": p.id, "name": p.name} for p in products.values()]
        payload = build_fallback_recipes(
            manifest, inventory, request.scanned_product_id, request.cuisine
        )
    database.add(
        AIRequest(
            kind="recipes",
            model=provider,
            latency_ms=int((time.monotonic() - started) * 1000),
            valid=not used_fallback,
            used_fallback=used_fallback,
        )
    )
    database.commit()
    stocked = set(products) | {row["product_id"] for row in manifest}
    return {
        "recipes": _with_locations(payload, locations, stocked),
        "missing_ingredients": missing,
        "used_fallback": used_fallback,
    }
