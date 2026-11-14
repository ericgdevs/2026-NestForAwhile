from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

MATRIX_PATH = Path(__file__).with_name("clinical_rules_matrix.json")
with MATRIX_PATH.open(encoding="utf-8") as matrix_file:
    _MATRIX = json.load(matrix_file)
RULES = _MATRIX["rules"]
# ICD-10 code -> {"label", "choices"}; codes are the stored medical data (encrypted at rest).
CONDITIONS = {code: entry for code, entry in _MATRIX["conditions"].items() if code != "_note"}

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


def conditions_to_choices(icd10_codes: list[str]) -> list[str]:
    """Map a member's ICD-10 codes to dietary choices through the matrix (rules, never AI)."""
    unknown = set(icd10_codes).difference(CONDITIONS)
    if unknown:
        raise ValueError(f"Unknown ICD-10 code(s): {', '.join(sorted(unknown))}")
    return sorted({choice for code in icd10_codes for choice in CONDITIONS[code]["choices"]})


def household_label(product: Any, members: list[Any]) -> dict[str, Any]:
    """One label for the household: Green if no one is restricted, Yellow if some, Red if all.

    Each member is a mapping or object with nickname, restrictions, and allergies.
    """
    if not members:
        return {
            "status": CAPPED,
            "explanation": "We don't have your household's dietary choices yet.",
            "not_for": [],
            "allergy_match": False,
        }
    not_for, capped_reasons, allergy_match = [], [], False
    for member in members:
        restrictions = _normalise_values(_value(member, "restrictions"))
        allergies = _normalise_values(_value(member, "allergies"))
        blocked = []
        for choice in sorted(restrictions | allergies):
            kind = "allergies" if choice in allergies else "restrictions"
            status, explanation = classify(product, {kind: [choice]})
            if status == RESTRICTED:
                blocked.append(choice)
                allergy_match = allergy_match or choice in allergies
            elif status == CAPPED:
                capped_reasons.append(explanation)
        if blocked:
            not_for.append({"nickname": _value(member, "nickname"), "reason": ", ".join(blocked)})

    if len(not_for) == len(members):
        status, explanation = RESTRICTED, "Not recommended for anyone in your household."
    elif not_for:
        names = ", ".join(entry["nickname"] for entry in not_for)
        status, explanation = CAPPED, f"Fine for some of your household, but not for {names}."
    elif capped_reasons:
        status, explanation = CAPPED, capped_reasons[0]
    else:
        status, explanation = APPROVED, "This item fits everyone in your household."
    return {
        "status": status,
        "explanation": explanation,
        "not_for": not_for,
        "allergy_match": allergy_match,
    }
