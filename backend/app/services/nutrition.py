from __future__ import annotations

from types import SimpleNamespace

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models import Client, Product
from app.rules.classify import APPROVED, CAPPED, RESTRICTED, household_label
from app.services.external_common import LookupFailed
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
        field: getattr(product, field) for field in ("sku", "allergens", "diet_flags", *NUTRIENTS)
    }
    return {
        "sku": product.sku,
        **{field: product_data[field] for field in NUTRIENTS},
        **{field: getattr(product, field) for field in DISPLAY_FIELDS},
        **safety_label(product_data, members),
    }


# Display only: they never change the status. Left empty (None) when no source has a value.
DISPLAY_FIELDS = (
    "calories", "carbs_g", "serving_size_g", "total_fat_g", "trans_fat_g", "cholesterol_mg",
    "fiber_g", "added_sugar_g", "protein_g", "vitamin_d_mcg", "calcium_mg", "iron_mg",
)  # fmt: skip
SCAN_FIELDS = (*NUTRIENTS, *DISPLAY_FIELDS)
NOT_STOCKED = "Not stocked at Epic Cure today."
LOOKUP_FAILED = "We couldn't look this item up. Try again, or ask a volunteer."
EXTERNAL_SWAPS = 3
# Words in OFF/USDA categories or the product name -> our catalog category (for swaps).
CATEGORY_WORDS = (
    ("Beverages", ("beverage", "drink", "soda", "juice", "water", "tea", "coffee")),
    ("Dairy", ("dairy", "milk", "cheese", "yogurt", "butter")),
    ("Snacks", ("snack", "candy", "candies", "chocolate", "confection", "biscuit", "cookie",
                "chip", "cracker", "bar")),
    ("Canned Goods", ("canned", "soup", "preserved")),
    ("Grains", ("cereal", "bread", "pasta", "rice", "grain", "flour", "oat")),
    ("Proteins", ("meat", "poultry", "fish", "egg", "legume", "nut", "seed", "tofu")),
    ("Produce", ("fruit", "vegetable", "produce")),
    ("Pantry", ("sauce", "oil", "condiment", "spice", "sweetener", "syrup")),
)  # fmt: skip


def lookup_external(code: str) -> tuple[dict[str, object] | None, bool]:
    """(product data or None, lookup failed). A failure in one service still tries the other."""
    failed = False
    for lookup in (lookup_open_food_facts, lookup_usda):
        try:
            if found := lookup(code):
                return found, False
        except LookupFailed:
            failed = True
    return None, failed


def external_category(enrichment: dict[str, object]) -> str | None:
    text = " ".join([*(enrichment.get("categories") or []), str(enrichment.get("name") or "")])
    text = text.lower()
    return next((cat for cat, words in CATEGORY_WORDS if any(w in text for w in words)), None)


def _trace_names(flags: list[str]) -> str:
    return ", ".join(flag.removeprefix("contains_").replace("_", " ") for flag in flags)


def external_label(data: dict[str, object], members: list[dict[str, object]]) -> dict[str, object]:
    """Same rules engine as catalog items, then stricter: an item we don't stock is never Approved.

    Any household member's allergy match is Restricted; traces are at least Capped.
    """
    label = safety_label(data, members)
    traces = data.get("traces") or []
    if label["allergy_match"]:
        who = "; ".join(f"{e['nickname']}: {e['reason']}" for e in label["not_for"])
        label["status"], label["explanation"] = RESTRICTED, f"Not for {who}."
    elif traces:
        risky = household_label(
            {**data, "allergens": [*(data["allergens"] or []), *traces],
             "diet_flags": [*(data["diet_flags"] or []), *traces]},
            members,
        )  # fmt: skip
        if risky["allergy_match"]:
            names = ", ".join(e["nickname"] for e in risky["not_for"])
            label.update(
                status=RESTRICTED if label["status"] == RESTRICTED else CAPPED,
                explanation=f"May contain traces of {_trace_names(traces)}. Check before "
                f"giving it to {names}.",
                not_for=risky["not_for"],
                allergy_match=True,
            )
    if label["status"] == APPROVED:
        label["status"], label["explanation"] = CAPPED, "We can't fully confirm this item."
    label["explanation"] = f"{label['explanation']} {NOT_STOCKED}"
    return label


def scan_external(
    database: Session, code: str, members: list[dict[str, object]]
) -> dict[str, object] | None:
    enrichment, failed = lookup_external(code)
    if enrichment is None:
        if not failed:
            return None  # nobody knows this code: the route answers 404
        return {
            "product_id": None, "sku": code, "barcode": code, "name": f"Scanned product {code}",
            "image_url": None, **dict.fromkeys(SCAN_FIELDS),
            "status": CAPPED, "explanation": LOOKUP_FAILED, "not_for": [],
            "allergy_match": False, "swaps": [],
        }  # fmt: skip
    data = {
        "barcode": code,
        "sku": code,
        "name": enrichment.get("name") or f"Scanned product {code}",
        "image_url": enrichment.get("image_url"),
        **{field: enrichment.get(field) for field in SCAN_FIELDS},
        "allergens": enrichment.get("allergens"),
        "diet_flags": enrichment.get("diet_flags"),
        "traces": enrichment.get("traces", []),
    }
    label = external_label(data, members)
    category = SimpleNamespace(id=None, category=external_category(enrichment))
    swaps = find_swaps(database, category, members, EXTERNAL_SWAPS)
    return {
        "product_id": None,
        **{k: data[k] for k in ("sku", "barcode", "name", "image_url", *SCAN_FIELDS)},
        **label,
        "swaps": swaps,
    }


def scan_local(database: Session, code: str, client: Client) -> dict[str, object] | None:
    product = database.scalar(
        select(Product).where(or_(Product.barcode == code, Product.sku == code))
    )
    members = members_for(client)
    if product is None:
        return scan_external(database, code, members)

    product_data = {
        field: getattr(product, field)
        for field in (
            "barcode",
            "sku",
            "name",
            "image_url",
            "allergens",
            "diet_flags",
            *SCAN_FIELDS,
        )
    }
    if any(product_data[field] is None for field in NUTRIENTS):
        enrichment, _ = lookup_external(product.barcode)
        for field in SCAN_FIELDS:  # fill gaps only; stored allergens and name always win
            if product_data[field] is None and enrichment:
                product_data[field] = enrichment.get(field)
    label = safety_label(product_data, members)
    swaps = find_swaps(database, product, members) if label["status"] == RESTRICTED else []
    return {
        "product_id": product.id,
        **{k: product_data[k] for k in ("sku", "barcode", "name", "image_url", *SCAN_FIELDS)},
        **label,
        "swaps": swaps,
    }
