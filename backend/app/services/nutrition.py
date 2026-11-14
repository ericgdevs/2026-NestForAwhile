from __future__ import annotations

import json

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models import Client, Product
from app.rules.classify import classify


def scan_local(database: Session, code: str, client: Client) -> dict[str, object] | None:
    product = database.scalar(
        select(Product).where(or_(Product.barcode == code, Product.sku == code))
    )
    if product is None:
        return None
    profile = client.dietary_profile
    profile_data = {
        "restrictions": json.loads(profile.restrictions) if profile else [],
        "allergies": json.loads(profile.allergies) if profile else [],
    }
    status, explanation = classify(product, profile_data)
    if any(
        getattr(product, field) is None
        for field in ("sodium_mg", "sugar_g", "sat_fat_g", "potassium_mg")
    ):
        status = "Capped"
        explanation = "We couldn't confirm all nutrition details for this item."
    return {
        "product_id": product.id,
        "sku": product.sku,
        "barcode": product.barcode,
        "name": product.name,
        "image_url": product.image_url,
        "sodium_mg": product.sodium_mg,
        "sugar_g": product.sugar_g,
        "sat_fat_g": product.sat_fat_g,
        "potassium_mg": product.potassium_mg,
        "status": status,
        "explanation": explanation,
    }
