from __future__ import annotations

RECIPE_INSTRUCTIONS = (
    "Create 1-6 safe recipes using only the supplied manifest items. "
    "Never use an item whose status is Restricted. "
    "If focus_index is set, every recipe must use that item. "
    "Give each recipe a short cuisine name (e.g. Mexican, Italian, Asian, Southern) and spread "
    "recipes across different cuisines; if cuisine is set, use only that cuisine. "
    'Return JSON: {"recipes": [{"title": str, "cuisine": str, "ingredients": [{"name": str, '
    '"product_id": <manifest index or null>}], "steps": [str]}]}.'
)


# Groq structured outputs (strict): every key required, nothing extra, no length keywords.
RECIPE_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "recipes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "cuisine": {"type": "string"},
                    "ingredients": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "product_id": {"type": ["integer", "null"]},
                            },
                            "required": ["name", "product_id"],
                            "additionalProperties": False,
                        },
                    },
                    "steps": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["title", "cuisine", "ingredients", "steps"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["recipes"],
    "additionalProperties": False,
}


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
