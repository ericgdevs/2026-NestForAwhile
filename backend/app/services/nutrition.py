from __future__ import annotations

import json

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models import Client, Product
from app.rules.classify import classify
from app.services.off import lookup_open_food_facts
from app.services.usda import lookup_usda

NUTRIENTS = ("sodium_mg", "sugar_g", "sat_fat_g", "potassium_mg")


def profile_for(client: Client | None) -> dict[str, list[str]]:
    profile = client.dietary_profile if client else None
    return {
        "restrictions": json.loads(profile.restrictions) if profile else [],
        "allergies": json.loads(profile.allergies) if profile else [],
    }


def safety_label(
    product_data: dict[str, object], profile_data: dict[str, list[str]]
) -> tuple[str, str]:
    """Rules-engine status; missing nutrition is never shown as Approved."""
    status, explanation = classify(product_data, profile_data)
    if any(product_data.get(field) is None for field in NUTRIENTS):
        status = "Capped"
        explanation = "We couldn't confirm all nutrition details for this item."
    return status, explanation


def local_label(product: Product, profile_data: dict[str, list[str]]) -> dict[str, object]:
    """Stored nutrition and rules status for a warehouse product; no outside lookups."""
    product_data = {
        field: getattr(product, field)
        for field in ("sku", "allergens", "diet_flags", *NUTRIENTS)
    }
    status, explanation = safety_label(product_data, profile_data)
    return {
        "sku": product.sku,
        **{field: product_data[field] for field in NUTRIENTS},
        "status": status,
        "explanation": explanation,
    }


def scan_local(database: Session, code: str, client: Client) -> dict[str, object] | None:
    product = database.scalar(
        select(Product).where(or_(Product.barcode == code, Product.sku == code))
    )
    profile_data = profile_for(client)
    enrichment = None
    if product is None:
        enrichment = lookup_open_food_facts(code) or lookup_usda(code)
        if enrichment is None:
            return None
        product_data = {
            "barcode": code,
            "sku": code,
            "name": enrichment.get("name") or f"Scanned product {code}",
            "image_url": enrichment.get("image_url"),
            "sodium_mg": enrichment.get("sodium_mg"),
            "sugar_g": enrichment.get("sugar_g"),
            "sat_fat_g": enrichment.get("sat_fat_g"),
            "potassium_mg": enrichment.get("potassium_mg"),
            "allergens": enrichment.get("allergens", []),
            "diet_flags": enrichment.get("diet_flags", []),
        }
        classification_product = product_data
    else:
        product_data = {
            field: getattr(product, field)
            for field in (
                "barcode",
                "sku",
                "name",
                "image_url",
                "sodium_mg",
                "sugar_g",
                "sat_fat_g",
                "potassium_mg",
                "allergens",
                "diet_flags",
            )
        }
        if any(
            product_data[field] is None
            for field in ("sodium_mg", "sugar_g", "sat_fat_g", "potassium_mg")
        ):
            enrichment = lookup_open_food_facts(product.barcode) or lookup_usda(product.barcode)
            if enrichment:
                product_data.update(
                    {field: value for field, value in enrichment.items() if value is not None}
                )
        classification_product = product_data

    status, explanation = safety_label(classification_product, profile_data)
    return {
        "product_id": product.id if product else None,
        "sku": product_data["sku"],
        "barcode": product_data["barcode"],
        "name": product_data["name"],
        "image_url": product_data["image_url"],
        "sodium_mg": product_data["sodium_mg"],
        "sugar_g": product_data["sugar_g"],
        "sat_fat_g": product_data["sat_fat_g"],
        "potassium_mg": product_data["potassium_mg"],
        "status": status,
        "explanation": explanation,
    }
