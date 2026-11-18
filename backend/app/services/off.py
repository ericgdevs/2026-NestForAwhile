from __future__ import annotations

from typing import Any

import httpx

from app.services.external_common import LookupFailed, map_allergens, serving_amount, to_number

OFF_URL = "https://world.openfoodfacts.org/api/v2/product/{barcode}.json"
TIMEOUT_SECONDS = 3.0
_CACHE: dict[str, dict[str, Any] | None] = {}


def _salt_as_sodium(nutriments: dict[str, Any]) -> dict[str, Any]:
    """OFF often has salt but no sodium; sodium = salt / 2.5 (both in grams)."""
    out = dict(nutriments)
    for suffix in ("_serving", "_100g"):
        salt = to_number(out.get(f"salt{suffix}"))
        if out.get(f"sodium{suffix}") is None and salt is not None:
            out[f"sodium{suffix}"] = salt / 2.5
    return out


def lookup_open_food_facts(
    barcode: str, client: httpx.Client | None = None
) -> dict[str, Any] | None:
    """Product data on our basis, None if OFF doesn't know the code, LookupFailed on errors."""
    if barcode in _CACHE:
        return _CACHE[barcode]
    owns_client = client is None
    http_client = client or httpx.Client(timeout=TIMEOUT_SECONDS)
    try:
        response = http_client.get(OFF_URL.format(barcode=barcode))
        if response.status_code == 404:  # OFF answers 404 for an unknown barcode
            _CACHE[barcode] = None
            return None
        response.raise_for_status()
        payload = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise LookupFailed(type(exc).__name__) from exc  # failures are never cached
    finally:
        if owns_client:
            http_client.close()
    if payload.get("status") != 1:
        _CACHE[barcode] = None
        return None
    product = payload.get("product", {})
    nutriments = _salt_as_sodium(product.get("nutriments", {}))
    serving_g = to_number(product.get("serving_quantity"))
    ingredients = product.get("ingredients_text") or product.get("ingredients_text_en")

    def amount(key: str, factor: float = 1.0) -> float | None:
        return serving_amount(nutriments, key, serving_g, factor)

    result = {
        "barcode": barcode,
        "name": product.get("product_name") or product.get("product_name_en"),
        "image_url": product.get("image_front_url"),
        "ingredients_text": ingredients,
        **map_allergens(product.get("allergens_tags"), product.get("traces_tags"), ingredients),
        "categories": product.get("categories_tags") or [],
        "sodium_mg": amount("sodium", 1000),  # OFF: grams
        "sugar_g": amount("sugars"),
        "sat_fat_g": amount("saturated-fat"),
        "potassium_mg": amount("potassium", 1000),  # OFF: grams
        "calories": amount("energy-kcal"),
        "carbs_g": amount("carbohydrates"),
        "serving_size_g": serving_g,
        "total_fat_g": amount("fat"),
        "trans_fat_g": amount("trans-fat"),
        "cholesterol_mg": amount("cholesterol", 1000),  # OFF: grams
        "fiber_g": amount("fiber"),
        "protein_g": amount("proteins"),
        "added_sugar_g": amount("added-sugars"),
        "vitamin_d_mcg": amount("vitamin-d", 1_000_000),  # OFF: grams
        "calcium_mg": amount("calcium", 1000),  # OFF: grams
        "iron_mg": amount("iron", 1000),  # OFF: grams
        "source": "openfoodfacts",
    }
    _CACHE[barcode] = result
    return result
