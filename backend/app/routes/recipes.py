from __future__ import annotations

import json
import time

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.fallback import build_fallback_recipes
from app.ai.provider import provider_from_settings
from app.ai.recipes import build_recipe_prompt
from app.ai.schemas import validate_recipe_output
from app.auth import Role, require_roles
from app.db import get_db
from app.models import AIRequest, Client, InventoryLot, Product, User
from app.services.cart import active_session, build_manifest, get_or_create_cart
from app.services.recipe_guard import guard_recipes

router = APIRouter()


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
    inventory_rows = database.scalars(
        select(InventoryLot).where(InventoryLot.quantity > 0)
    ).all()
    product_ids = {row.product_id for row in inventory_rows}
    products = {
        product.id: product
        for product in database.scalars(select(Product).where(Product.id.in_(product_ids)))
    }
    inventory = [
        {"product_id": product.id, "name": product.name}
        for product in products.values()
    ]
    profile = client.dietary_profile if client else None
    restrictions = json.loads(profile.restrictions) if profile else []
    payload = None
    used_fallback = False
    try:
        generated = provider_from_settings().generate(
            build_recipe_prompt(manifest, None, inventory, restrictions),
            {"type": "object"},
        )
        validated = validate_recipe_output(generated, product_ids)
        guarded = guard_recipes(
            [recipe.model_dump() for recipe in validated.recipes],
            products,
            {"restrictions": restrictions, "allergies": []},
            product_ids,
        )
        if guarded:
            payload = guarded
    except Exception:
        used_fallback = True
    if payload is None:
        payload = build_fallback_recipes(manifest, inventory)
        used_fallback = True
    database.add(
        AIRequest(
            kind="recipes",
            model="fallback" if used_fallback else "configured",
            latency_ms=int((time.monotonic() - started) * 1000),
            valid=not used_fallback,
            used_fallback=used_fallback,
        )
    )
    database.commit()
    return {"recipes": payload, "used_fallback": used_fallback}
