from __future__ import annotations

RECIPE_INSTRUCTIONS = (
    "Create 1-3 safe recipes using only the supplied manifest items. "
    "Never use an item whose status is Restricted. "
    'Return JSON: {"recipes": [{"title": str, "ingredients": [{"name": str, "product_id": '
    '<manifest index or null>}], "steps": [str]}]}.'
)


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
