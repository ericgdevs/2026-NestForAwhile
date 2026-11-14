from __future__ import annotations

from collections.abc import Iterable

DIETARY_TIER_IDS = {
    "Low Sugar": 2,
    "Low Sodium": 3,
    "Heart Healthy": 4,
    "Kidney Friendly": 5,
    "Vegetarian": 6,
    "Vegan": 7,
    "Gluten Free": 8,
    "Nut Allergy": 9,
    "Dairy Free": 10,
}


def dietary_tier_id(restrictions: Iterable[str]) -> int:
    """Return the strictest fixed tier for a client's selected restrictions."""
    selected = set(restrictions)
    unknown = selected.difference(DIETARY_TIER_IDS)
    if unknown:
        raise ValueError(f"Unknown dietary restriction(s): {', '.join(sorted(unknown))}")
    return max((DIETARY_TIER_IDS[name] for name in selected), default=1)
