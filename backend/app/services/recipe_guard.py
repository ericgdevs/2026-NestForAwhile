from __future__ import annotations

from collections.abc import Iterable

from app.rules.classify import RESTRICTED, classify


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
