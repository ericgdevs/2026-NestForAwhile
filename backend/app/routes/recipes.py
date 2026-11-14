from __future__ import annotations

import json
import time

from fastapi import APIRouter, Depends
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
from app.rules.classify import RESTRICTED, classify
from app.services.cart import active_session, build_manifest, get_or_create_cart
from app.services.recipe_guard import guard_recipes

router = APIRouter()


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


def _ai_suggestions(products, locations, cart, profile_data, household_size):
    """Recipes plus missing-ingredient suggestions; raises if the AI cannot give a safe recipe."""
    items = list(products.values())
    restrictions = [*profile_data["restrictions"], *profile_data["allergies"]]
    quantities = {row["product_id"]: row["quantity"] for row in cart}
    manifest, index_map = build_ai_manifest(items, restrictions, quantities, household_size)
    in_stock = set(products)

    def run(task):
        result = run_ai_task(task, items, restrictions, quantities, household_size)
        return result, apply_rules_guard(result, manifest, items, restrictions, in_stock).output

    result, output = run(AITask.RECIPES)
    recipes = guard_recipes(
        [
            {
                "title": recipe.title,
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
    if not recipes:
        raise AIOrchestrationError("no safe recipes")
    try:
        _, missing_output = run(AITask.MISSING_INGREDIENTS)
    except Exception:
        missing_output = None  # missing-ingredient hints are optional; recipes still ship
    missing = [
        {
            "product_id": index_map[item.product_id],
            "name": items[item.product_id].name,
            "reason": item.reason,
            "location": locations[index_map[item.product_id]],
        }
        for item in (missing_output.items if missing_output else [])
    ]
    return result.provider, recipes, missing


@router.post("/recipes")
def recipes(
    current_user: User = Depends(require_roles(Role.CLIENT)),
    database: Session = Depends(get_db),
):
    started = time.monotonic()
    client = database.get(Client, current_user.id)
    session = active_session(database, client) if client else None
    cart = get_or_create_cart(database, session) if session else None
    manifest = build_manifest(database, cart) if cart else []
    profile = client.dietary_profile if client else None
    profile_data = {
        "restrictions": json.loads(profile.restrictions) if profile else [],
        "allergies": json.loads(profile.allergies) if profile else [],
    }
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
        )
    except Exception:
        pass  # any AI failure falls through to the deterministic fallback below
    used_fallback = payload is None
    if used_fallback:
        inventory = [{"product_id": p.id, "name": p.name} for p in products.values()]
        payload = build_fallback_recipes(manifest, inventory)
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
    return {"recipes": payload, "missing_ingredients": missing, "used_fallback": used_fallback}
