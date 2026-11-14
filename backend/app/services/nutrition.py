from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models import Client, Product
from app.rules.classify import household_label
from app.services.household import effective_choices
from app.services.off import lookup_open_food_facts
from app.services.swaps import find_swaps
from app.services.usda import lookup_usda

NUTRIENTS = ("sodium_mg", "sugar_g", "sat_fat_g", "potassium_mg")


def members_for(client: Client | None) -> list[dict[str, object]]:
    """Members for the rules engine: nickname, age, effective choices (codes stay server-side)."""
    return [
        {"nickname": member.nickname, "age": member.age, **effective_choices(member)}
        for member in (client.members if client else [])
    ]


def household_choices(client: Client | None) -> dict[str, list[str]]:
    """Every member's choices combined: restricted here means restricted for someone."""
    members = members_for(client)
    return {
        kind: sorted({choice for member in members for choice in member[kind]})
        for kind in ("restrictions", "allergies")
    }


def safety_label(product_data: dict[str, object], members: list[dict[str, object]]) -> dict:
    """Household label from the rules engine; missing nutrition is never shown as Approved."""
    label = household_label(product_data, members)
    if label["status"] == "Approved" and any(
        product_data.get(field) is None for field in NUTRIENTS
    ):
        label["status"] = "Capped"
        label["explanation"] = "We couldn't confirm all nutrition details for this item."
    return label


def local_label(product: Product, members: list[dict[str, object]]) -> dict[str, object]:
    """Stored nutrition and rules status for a warehouse product; no outside lookups."""
    product_data = {
        field: getattr(product, field)
        for field in ("sku", "allergens", "diet_flags", *NUTRIENTS)
    }
    return {
        "sku": product.sku,
        **{field: product_data[field] for field in NUTRIENTS},
        **safety_label(product_data, members),
    }


def scan_local(database: Session, code: str, client: Client) -> dict[str, object] | None:
    product = database.scalar(
        select(Product).where(or_(Product.barcode == code, Product.sku == code))
    )
    members = members_for(client)
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

    label = safety_label(classification_product, members)
    swaps = (
        find_swaps(database, product, members)
        if product is not None and label["status"] == "Restricted"
        else []
    )
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
        **label,
        "swaps": swaps,
    }
