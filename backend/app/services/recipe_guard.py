from __future__ import annotations

import re
from collections.abc import Iterable

from app.rules.classify import RESTRICTED, classify

# Free basics safe for every supported diet; they need no product_id. Not salt, sugar, honey,
# syrup, soy sauce, bouillon, butter, oil or milk. The name must be only these, optionally with a
# plain descriptor ("fresh basil", "ground cumin"), so "salt and black pepper" is still dropped.
FREE_BASICS = (
    "water|ice|black pepper|ground pepper|basil|oregano|parsley|cilantro|thyme|rosemary|dill"
    "|garlic powder|onion powder|cinnamon|cumin|paprika|chili powder|vinegar|lemon juice|lime juice"
)
DESCRIPTORS = "fresh|dried|dry|chopped|minced|ground|freshly|cold|warm|hot|ice|cooking|distilled"
FREE_BASIC_NAME = re.compile(rf"(?:(?:{DESCRIPTORS})\s+)*(?:{FREE_BASICS})", re.I)


def is_free_basic(name: object) -> bool:
    return isinstance(name, str) and FREE_BASIC_NAME.fullmatch(name.strip()) is not None


def guard_recipes(
    recipes: Iterable[dict],
    products: dict[int, object],
    profile: object,
    available_ids: set[int],
) -> list[dict]:
    safe = []
    for recipe in recipes:
        valid = True
        for ingredient in recipe["ingredients"]:
            product_id = ingredient.get("product_id")
            if product_id is None and is_free_basic(ingredient.get("name")):
                continue  # kept as-is, with no location
            if product_id is None or product_id not in available_ids:
                valid = False
                break
            product = products.get(product_id)
            if product is None or classify(product, profile)[0] == RESTRICTED:
                valid = False
                break
        if valid:
            safe.append(recipe)
    return safe
