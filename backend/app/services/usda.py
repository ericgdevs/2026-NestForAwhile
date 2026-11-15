from __future__ import annotations

from typing import Any

import httpx

from app.config import Settings
from app.services.external_common import LookupFailed, map_allergens

USDA_SEARCH_URL = "https://api.nal.usda.gov/fdc/v1/foods/search"
_CACHE: dict[str, dict[str, Any] | None] = {}


def _nutrients(food: dict[str, Any]) -> dict[str, float | None]:
    """USDA values are per 100 g (mg, or g for sugar/fat/carbs, kcal for energy).

    Scaled to the serving size when USDA gives it in grams, so the rules engine sees per-serving.
    """
    values: dict[str, float | None] = {
        "sodium_mg": None,
        "sugar_g": None,
        "sat_fat_g": None,
        "potassium_mg": None,
        "calories": None,
        "carbs_g": None,
    }
    nutrient_map = {
        1093: "sodium_mg",
        269: "sugar_g",
        1258: "sat_fat_g",
        1092: "potassium_mg",
        1008: "calories",
        1005: "carbs_g",
    }
    serving = food.get("servingSize")
    in_grams = str(food.get("servingSizeUnit", "")).lower() in ("g", "grm")
    scale = serving / 100 if in_grams and isinstance(serving, int | float) and serving > 0 else 1
    for nutrient in food.get("foodNutrients", []):
        target = nutrient_map.get(nutrient.get("nutrientId"))
        if target and nutrient.get("value") is not None:
            values[target] = round(nutrient["value"] * scale, 2)
    return values


def lookup_usda(barcode: str, client: httpx.Client | None = None) -> dict[str, Any] | None:
    if barcode in _CACHE:
        return _CACHE[barcode]
    api_key = Settings.from_env().usda_api_key
    if not api_key:
        return None
    owns_client = client is None
    http_client = client or httpx.Client(timeout=3.0)
    try:
        response = http_client.get(
            USDA_SEARCH_URL,
            params={"api_key": api_key, "query": barcode, "pageSize": 1},
        )
        response.raise_for_status()
        foods = response.json().get("foods", [])
    except (httpx.HTTPError, ValueError) as exc:
        raise LookupFailed(type(exc).__name__) from exc  # failures are never cached
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
        **map_allergens(None, None, food.get("ingredients")),
        "categories": [food.get("foodCategory") or ""],
        "source": "usda",
        **_nutrients(food),
    }
    _CACHE[barcode] = result
    return result
