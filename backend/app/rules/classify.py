from dataclasses import dataclass
from enum import IntEnum

from app.rules.matrix import load_matrix

UNKNOWN_REASON = "We couldn't confirm this one — please ask a volunteer."


class Status(IntEnum):
    APPROVED = 0
    CAPPED = 1
    RESTRICTED = 2


@dataclass(frozen=True)
class Classification:
    status: Status
    reason: str


APPROVED = Classification(Status.APPROVED, "This fits your dietary needs.")


def _exclusion(product, restriction: str, rule: dict) -> Classification | None:
    allergens = {a.lower() for a in product.allergens or []}
    flags = set(product.diet_flags or [])
    hit = (allergens & set(rule.get("forbidden_allergens", []))) or (flags & set(rule.get("forbidden_flags", [])))
    if hit:
        return Classification(Status.RESTRICTED, f"Not suitable for {restriction}.")
    return None


def _has_exclusion_data(product) -> bool:
    return bool(product.allergens or product.diet_flags or product.ingredients_text)


def _limits(product, restriction: str, rule: dict) -> Classification | None:
    result = None
    for limit in rule.get("limits", []):
        value = getattr(product, limit["nutrient"], None)
        if value is None:
            found = Classification(Status.CAPPED, UNKNOWN_REASON)
        elif value > limit["restricted_above"]:
            found = Classification(Status.RESTRICTED, f"Too high in {limit['nutrient']} for {restriction}.")
        elif value > limit["capped_above"]:
            found = Classification(Status.CAPPED, f"Limit this one for {restriction}: {limit['nutrient']} is on the high side.")
        else:
            continue
        if result is None or found.status > result.status:
            result = found
    return result


def classify(product, restrictions: list[str]) -> Classification:
    """Strictest result across all restrictions wins; allergen/exclusion hits are always Restricted."""
    rules = load_matrix()["restrictions"]
    worst = APPROVED
    for restriction in restrictions:
        rule = rules[restriction]
        found = _exclusion(product, restriction, rule) or _limits(product, restriction, rule)
        if found is None and ("forbidden_flags" in rule or "forbidden_allergens" in rule) and not _has_exclusion_data(product):
            found = Classification(Status.CAPPED, UNKNOWN_REASON)
        if found and found.status > worst.status:
            worst = found
    return worst
