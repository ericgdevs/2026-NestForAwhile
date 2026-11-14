from __future__ import annotations

from typing import Any

import httpx

OFF_URL = "https://world.openfoodfacts.org/api/v2/product/{barcode}.json"
_CACHE: dict[str, dict[str, Any] | None] = {}


def lookup_open_food_facts(
    barcode: str, client: httpx.Client | None = None
) -> dict[str, Any] | None:
    if barcode in _CACHE:
        return _CACHE[barcode]
    owns_client = client is None
    http_client = client or httpx.Client(timeout=2.0)
    try:
        response = http_client.get(OFF_URL.format(barcode=barcode))
        response.raise_for_status()
        payload = response.json()
    except (httpx.HTTPError, ValueError):
        _CACHE[barcode] = None
        return None
    finally:
        if owns_client:
            http_client.close()
    if payload.get("status") != 1:
        _CACHE[barcode] = None
        return None
    product = payload.get("product", {})
    nutriments = product.get("nutriments", {})
    result = {
        "barcode": barcode,
        "name": product.get("product_name") or product.get("product_name_en"),
        "image_url": product.get("image_front_url"),
        "ingredients_text": product.get("ingredients_text"),
        "allergens": product.get("allergens_tags", []),
        "sodium_mg": nutriments.get("sodium_100g"),
        "sugar_g": nutriments.get("sugars_100g"),
        "sat_fat_g": nutriments.get("saturated-fat_100g"),
        "potassium_mg": nutriments.get("potassium_100g"),
        "source": "openfoodfacts",
    }
    _CACHE[barcode] = result
    return result
