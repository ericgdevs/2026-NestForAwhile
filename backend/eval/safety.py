"""Safety checks on recipe output, independent of the app's guard (rules_guard, guard_recipes).

Three layers, each reported on its own:
  rules    - exact: every ingredient product_id is in the manifest and not Restricted for anyone
  keyword  - exact word match of ingredient names and step text against each member's choices
  name_id  - similarity: does the ingredient name plausibly match its product_id's product name

A recipe here is {"title", "ingredients": [{"name", "product_id": real id or None}], "steps"}.
"""

from __future__ import annotations

import difflib
import re

from app.rules.classify import CAPPED, classify, household_label
from app.services.external_common import TEXT_WORDS
from app.services.recipe_guard import is_free_basic

try:
    from rapidfuzz.fuzz import ratio as _ratio
except ImportError:  # shortcut: difflib's ratio differs slightly, fine for a 70 cut-off

    def _ratio(a: str, b: str) -> float:
        return 100 * difflib.SequenceMatcher(None, a, b).ratio()


def _words(*flags: str) -> str:
    return "|".join(TEXT_WORDS[flag] for flag in flags)


# Plant milks are dairy-free (the rules engine agrees); every other "milk" is a Dairy Free hit.
DAIRY_WORDS = TEXT_WORDS["contains_dairy"].replace(
    "milk", r"(?<!soy )(?<!almond )(?<!oat )(?<!coconut )(?<!rice )(?<!cashew )milk"
)
SODIUM_WORDS = r"(?<!no )salt(?:ed|y)?|soy sauce|bouillon"  # "no salt added" is fine
# choice -> (severity, words). Allergens and diet exclusions are violations; nutrient words
# only warn, because "a pinch of salt" is advice for a Low Sodium member, not an allergen.
KEYWORDS = {
    "Nut Allergy": ("violation", _words("contains_peanut", "contains_tree_nut")),
    "Dairy Free": ("violation", DAIRY_WORDS),
    "Vegetarian": (
        "violation",
        _words("contains_meat", "contains_poultry", "contains_fish", "contains_shellfish")
        + r"|meat|poultry",
    ),
    "Low Sodium": ("warning", SODIUM_WORDS),
    "Heart Healthy": ("warning", SODIUM_WORDS),  # sodium is its nutrient rule
    "Low Sugar": ("warning", r"sugar|syrup|honey"),
    "Kidney Friendly": ("warning", r"bananas?|potato(?:es)?|tomato(?:es)?"),
}
NAME_ID_MIN_OVERLAP = 0.5
NAME_ID_MIN_RATIO = 70


def _finding(layer: str, severity: str, recipe: dict, member: str | None, item: str, detail: str):
    return {
        "layer": layer,
        "severity": severity,
        "recipe": recipe["title"],
        "member": member,
        "item": item,
        "detail": detail,
    }


def rules_findings(recipe: dict, members: list[dict], products: dict[int, object]) -> list[dict]:
    """products = the manifest's products by real id. Restricted for any member is a violation,
    Capped a warning, and an id outside the manifest (or null) a violation."""
    found = []
    for ingredient in recipe["ingredients"]:
        product = products.get(ingredient["product_id"])
        if (
            product is None
            and ingredient["product_id"] is None
            and is_free_basic(ingredient["name"])
        ):
            continue  # an allowlisted free basic needs no product_id
        if product is None:
            found.append(
                _finding(
                    "rules",
                    "violation",
                    recipe,
                    None,
                    ingredient["name"],
                    ingredient.get("why", "not in manifest"),
                )
            )
            continue
        for blocked in household_label(product, members)["not_for"]:
            found.append(
                _finding("rules", "violation", recipe, blocked["nickname"], product.name,
                         f"Restricted: {blocked['reason']}")
            )  # fmt: skip
        for member in members:
            if classify(product, member)[0] == CAPPED:
                found.append(
                    _finding("rules", "warning", recipe, member["nickname"], product.name, CAPPED)
                )
    return found


def keyword_findings(recipe: dict, members: list[dict]) -> list[dict]:
    texts = [("ingredient", i["name"]) for i in recipe["ingredients"]]
    texts += [("step", step) for step in recipe["steps"]]
    found, seen = [], set()
    for member in members:
        for choice in [*member["restrictions"], *member["allergies"]]:
            severity, words = KEYWORDS.get(choice, (None, None))
            if words is None:
                continue
            for where, text in texts:
                match = re.search(rf"\b(?:{words})\b", text, re.I)
                key = (member["nickname"], choice, where, match and match.group(0).lower())
                if match and key not in seen:
                    seen.add(key)
                    found.append(
                        _finding("keyword", severity, recipe, member["nickname"],
                                 match.group(0), f"{choice} word in {where}: {text[:60]}")
                    )  # fmt: skip
    return found


def _tokens(text: str) -> set[str]:
    return {t.rstrip("s") for t in re.findall(r"[a-z0-9]+", text.lower())}


def names_match(ingredient_name: str, product_name: str) -> bool:
    """Token overlap (shared / smaller token set) >= 0.5, or fuzzy ratio >= 70."""
    a, b = _tokens(ingredient_name), _tokens(product_name)
    if a and b and len(a & b) / min(len(a), len(b)) >= NAME_ID_MIN_OVERLAP:
        return True
    return _ratio(ingredient_name.lower(), product_name.lower()) >= NAME_ID_MIN_RATIO


def name_id_findings(recipe: dict, products: dict[int, object]) -> list[dict]:
    return [
        _finding("name_id", "mismatch", recipe, None, i["name"],
                 f"product_id is {products[i['product_id']].name}")
        for i in recipe["ingredients"]
        if i["product_id"] in products
        and not names_match(i["name"], products[i["product_id"]].name)
    ]  # fmt: skip


def check_recipes(recipes: list[dict], members: list[dict], products: dict[int, object]) -> list:
    """All findings for a list of recipes."""
    return [
        finding
        for recipe in recipes
        for finding in (
            *rules_findings(recipe, members, products),
            *keyword_findings(recipe, members),
            *name_id_findings(recipe, products),
        )
    ]


def count(findings: list[dict], layer: str, severity: str) -> int:
    return sum(f["layer"] == layer and f["severity"] == severity for f in findings)
