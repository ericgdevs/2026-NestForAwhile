from __future__ import annotations


def build_fallback_recipes(cart_manifest: list[dict], inventory: list[dict]) -> list[dict]:
    available = {item["product_id"]: item for item in inventory}
    ingredients = [
        {"name": item["name"], "product_id": item["product_id"]}
        for item in cart_manifest
        if item["product_id"] in available
    ]
    if not ingredients:
        return []
    return [
        {
            "title": "Simple pantry bowl",
            "ingredients": ingredients,
            "steps": ["Combine the available ingredients.", "Serve and adjust to taste."],
        }
    ]
