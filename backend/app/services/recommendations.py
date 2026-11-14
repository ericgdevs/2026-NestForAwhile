from __future__ import annotations

import json
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import Client, InventoryLot
from app.rules.classify import RESTRICTED, classify


def build_recommendations(database: Session, client: Client) -> list[dict[str, object]]:
    profile = client.dietary_profile
    profile_data = {
        "restrictions": json.loads(profile.restrictions) if profile else [],
        "allergies": json.loads(profile.allergies) if profile else [],
    }
    lots = database.scalars(
        select(InventoryLot)
        .options(joinedload(InventoryLot.product))
        .where(InventoryLot.quantity > 0, InventoryLot.expiration_date >= date.today())
    ).all()
    recommendations = []
    seen_products: set[int] = set()
    for lot in lots:
        product = lot.product
        if product.id in seen_products:
            continue
        status, rationale = classify(product, profile_data)
        if status == RESTRICTED:
            continue
        seen_products.add(product.id)
        recommendations.append(
            {
                "product_id": product.id,
                "name": product.name,
                "quantity": max(1, client.Household_Size),
                "status": status,
                "rationale": rationale,
                "aisle": lot.aisle,
                "shelf": lot.shelf,
                "bin": lot.bin,
            }
        )
    return recommendations
