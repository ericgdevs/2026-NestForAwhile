from __future__ import annotations

from typing import Any

import httpx

from app.config import Settings

USDA_SEARCH_URL = "https://api.nal.usda.gov/fdc/v1/foods/search"
_CACHE: dict[str, dict[str, Any] | None] = {}


def _nutrients(food: dict[str, Any]) -> dict[str, float | None]:
    values: dict[str, float | None] = {
        "sodium_mg": None,
        "sugar_g": None,
        "sat_fat_g": None,
        "potassium_mg": None,
    }
    nutrient_map = {
        1093: "sodium_mg",
        269: "sugar_g",
         1258: "sat_fat_g",
         1092: "potassium_mg",
    }
    for nutrient in food.get("foodNutrients", []):
        target = nutrient_map.get(nutrient.get("nutrientId"))
        if target:
            values[target] = nutrient.get("value")
    return values


def lookup_usda(barcode: str, client: httpx.Client | None = None) -> dict[str, Any] | None:
    if barcode in _CACHE:
        return _CACHE[barcode]
    api_key = Settings.from_env().usda_api_key
    if not api_key:
        return None
    owns_client = client is None
    http_client = client or httpx.Client(timeout=2.5)
    try:
        response = http_client.get(
            USDA_SEARCH_URL,
            params={"api_key": api_key, "query": barcode, "pageSize": 1},
        )
        response.raise_for_status()
        foods = response.json().get("foods", [])
    except (httpx.HTTPError, ValueError):
        _CACHE[barcode] = None
        return None
    finally:
        if owns_client:
            http_client.close()
    if not foods:
        _CACHE[barcode] = None
        return None
    food = foods[0]
    result = {
        "barcode": barcode,
        "name": food.get("description"),
        "image_url": None,
        "ingredients_text": food.get("ingredients"),
        "allergens": [],
        "source": "usda",
        **_nutrients(food),
    }
    _CACHE[barcode] = result
    return result
