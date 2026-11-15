"""Shared bits of the Open Food Facts and USDA lookups: failures, allergens, serving basis."""

from __future__ import annotations

import re
from typing import Any

# Allergen vocabulary the rules engine already uses (see seed catalog / classify.py).
OFF_TAGS = {
    "en:peanuts": "contains_peanut",
    "en:nuts": "contains_tree_nut",
    "en:milk": "contains_dairy",
    "en:eggs": "contains_egg",
    "en:gluten": "contains_gluten",
    "en:soybeans": "contains_soy",
    "en:fish": "contains_fish",
    "en:crustaceans": "contains_shellfish",
    "en:molluscs": "contains_shellfish",
}
# Word-boundary keywords for ingredient text ("nutmeg" must not match "nut").
TEXT_WORDS = {
    "contains_peanut": r"peanuts?",
    "contains_tree_nut": r"almonds?|cashews?|walnuts?|pecans?|hazelnuts?|pistachios?"
    r"|macadamias?|tree nuts?|nuts",
    "contains_dairy": r"milk|whey|casein|cheese|yogurt|lactose",
    "contains_egg": r"eggs?",
    "contains_gluten": r"wheat|barley|rye|gluten",
    "contains_soy": r"soy|soya|soybeans?",
    "contains_fish": r"fish|salmon|tuna|anchovy|anchovies|cod",
    "contains_shellfish": r"shrimp|crab|lobster|shellfish|prawns?",
    "contains_meat": r"beef|pork|bacon|ham|sausage|lard",
    "contains_poultry": r"chicken|turkey",
}
TRACE_MARKER = re.compile(r"may contain|contains traces|traces of|made in a facility", re.I)


class LookupFailed(RuntimeError):
    """The outside service could not be reached or answered badly (not the same as not found)."""


def text_flags(text: str | None) -> tuple[set[str], set[str]]:
    """(contains, may-contain) flags from ingredient text; text after a trace marker is traces."""
    text = text or ""
    marker = TRACE_MARKER.search(text)
    head, tail = (text[: marker.start()], text[marker.start() :]) if marker else (text, "")

    def scan(part: str) -> set[str]:
        return {
            flag for flag, words in TEXT_WORDS.items() if re.search(rf"\b(?:{words})\b", part, re.I)
        }

    return scan(head), scan(tail)


def map_allergens(
    allergen_tags: list[str] | None, trace_tags: list[str] | None, text: str | None
) -> dict[str, Any]:
    """Our allergen vocabulary; allergens/diet_flags are None when there is no allergen data."""
    contains, traces = text_flags(text)
    contains |= {OFF_TAGS[tag] for tag in allergen_tags or [] if tag in OFF_TAGS}
    traces |= {OFF_TAGS[tag] for tag in trace_tags or [] if tag in OFF_TAGS}
    known = bool(allergen_tags or trace_tags or (text or "").strip())
    allergens = sorted(f for f in contains if f != "contains_gluten" and f in _ALLERGEN_FLAGS)
    return {
        "allergens": allergens if known else None,
        "diet_flags": sorted(contains) if known else None,
        "traces": sorted(traces - contains),
    }


_ALLERGEN_FLAGS = {
    "contains_peanut", "contains_tree_nut", "contains_dairy", "contains_egg",
    "contains_soy", "contains_fish", "contains_shellfish",
}  # fmt: skip


def serving_amount(
    nutriments: dict[str, Any], key: str, serving_g: float | None, factor: float = 1.0
) -> float | None:
    """One nutrient on the basis the rules engine expects (per serving).

    Uses the per-serving value when given, else scales per-100 g by the serving size, else
    falls back to per-100 g as-is (shortcut: overstates small servings, so it errs cautious).
    `factor` converts the source unit (OFF gives sodium/potassium in grams) to ours (mg).
    """
    value = _number(nutriments.get(f"{key}_serving"))
    if value is None:
        per_100 = _number(nutriments.get(f"{key}_100g"))
        if per_100 is None:
            return None
        value = per_100 * serving_g / 100 if serving_g else per_100
    return round(value * factor, 2)


def _number(value: Any) -> float | None:
    try:
        return float(value) if value not in (None, "") else None
    except (TypeError, ValueError):
        return None


def to_number(value: Any) -> float | None:
    return _number(value)
