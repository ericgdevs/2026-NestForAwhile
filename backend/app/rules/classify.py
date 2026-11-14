from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

MATRIX_PATH = Path(__file__).with_name("clinical_rules_matrix.json")
with MATRIX_PATH.open(encoding="utf-8") as matrix_file:
    RULES = json.load(matrix_file)["rules"]

APPROVED = "Approved"
CAPPED = "Capped"
RESTRICTED = "Restricted"


def _value(source: Any, name: str, default: Any = None) -> Any:
    if isinstance(source, Mapping):
        return source.get(name, default)
    return getattr(source, name, default)


def _normalise_values(values: Any) -> set[str]:
    if values is None:
        return set()
    if isinstance(values, str):
        return {values}
    return set(values)


def _missing_relevant_data(product: Any, rule: dict[str, Any]) -> bool:
    if rule["nutrient"] is not None:
        return _value(product, rule["nutrient"]) is None
    flags = _value(product, "diet_flags")
    allergens = _value(product, "allergens")
    return flags is None or allergens is None


def classify(product: Any, profile: Any) -> tuple[str, str]:
    """Classify a product for a profile using the deterministic clinical matrix."""
    restrictions = _normalise_values(_value(profile, "restrictions"))
    allergies = _normalise_values(_value(profile, "allergies"))
    unknown = restrictions.union(allergies).difference(RULES)
    if unknown:
        raise ValueError(f"Unknown dietary option(s): {', '.join(sorted(unknown))}")

    flags = _normalise_values(_value(product, "diet_flags"))
    allergens = _normalise_values(_value(product, "allergens"))
    statuses: list[tuple[int, str]] = []

    for restriction in sorted(restrictions.union(allergies)):
        rule = RULES[restriction]
        if _missing_relevant_data(product, rule):
            statuses.append((1, f"We couldn't confirm this item for {restriction}."))
            continue

        if restriction in allergies:
            allergy_flag = {
                "Nut Allergy": {"contains_peanut", "contains_tree_nut"},
                "Dairy Free": {"contains_dairy"},
            }.get(restriction, set())
            if allergens.intersection(allergy_flag) or flags.intersection(allergy_flag):
                statuses.append(
                    (2, f"This item contains an ingredient restricted by {restriction}.")
                )
                continue

        excluded = set(rule["exclusions"])
        if flags.intersection(excluded):
            statuses.append((2, f"This item contains an ingredient restricted by {restriction}."))
            continue

        if rule["nutrient"] is not None:
            amount = _value(product, rule["nutrient"])
            if amount > rule["restricted_above"]:
                statuses.append((2, f"This item is above the {restriction} limit."))
            elif amount > rule["capped_above"]:
                statuses.append((1, f"This item is above the {restriction} guideline."))

    if any(severity == 2 for severity, _ in statuses):
        return RESTRICTED, next(reason for severity, reason in statuses if severity == 2)
    if statuses:
        return CAPPED, statuses[0][1]
    return APPROVED, "This item matches the selected dietary profile."
