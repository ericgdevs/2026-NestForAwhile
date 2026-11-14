from __future__ import annotations


def build_recipe_prompt(
    cart_manifest: list[dict],
    scanned_item: dict | None,
    inventory: list[dict],
    restrictions: list[str],
) -> str:
    return (
        "Create safe recipes using only the supplied products. "
        "Return JSON matching the recipe schema. "
        f"Restrictions: {restrictions}. "
        f"Cart: {cart_manifest}. "
        f"Scanned item: {scanned_item}. "
        f"In-stock inventory: {inventory}."
    )
