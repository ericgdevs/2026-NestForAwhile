from __future__ import annotations

# Deterministic recipes for when AI is off or unsafe; cuisine-tagged so cuisine filters still work.
TEMPLATES = (
    (
        "Simple pantry bowl",
        "American",
        ["Combine the available ingredients.", "Serve and adjust to taste."],
    ),
    (
        "Quick stir-fry",
        "Asian",
        ["Cut ingredients into bite-size pieces.", "Stir-fry over high heat for 5-7 minutes."],
    ),
    (
        "Warm burrito bowl",
        "Mexican",
        ["Warm the ingredients in a pan.", "Layer in a bowl and serve."],
    ),
)


def build_fallback_recipes(
    cart_manifest: list[dict],
    inventory: list[dict],
    focus_product_id: int | None = None,
    cuisine: str | None = None,
) -> list[dict]:
    available = {item["product_id"]: item for item in inventory}
    wanted = [focus_product_id] if focus_product_id is not None else []
    wanted += [item["product_id"] for item in cart_manifest if item["product_id"] not in wanted]
    ingredients = [
        {"name": available[pid]["name"], "product_id": pid} for pid in wanted if pid in available
    ]
    if not ingredients or (focus_product_id is not None and focus_product_id not in available):
        return []
    return [
        {"title": title, "cuisine": kind, "ingredients": ingredients, "steps": list(steps)}
        for title, kind, steps in TEMPLATES
        if cuisine is None or kind.lower() == cuisine.strip().lower()
    ]
