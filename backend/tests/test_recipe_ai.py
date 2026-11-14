from app.ai.fallback import build_fallback_recipes
from app.ai.recipes import build_recipe_prompt


def test_recipe_prompt_contains_plain_language_inputs():
    prompt = build_recipe_prompt(
        [{"product_id": 1, "name": "Synthetic oats"}],
        None,
        [{"product_id": 1, "name": "Synthetic oats"}],
        ["Low Sodium"],
    )
    assert "Restrictions: ['Low Sodium']" in prompt
    assert "Synthetic oats" in prompt


def test_fallback_uses_only_available_cart_items():
    result = build_fallback_recipes(
        [{"product_id": 1, "name": "Oats"}, {"product_id": 2, "name": "Missing"}],
        [{"product_id": 1, "name": "Oats"}],
    )
    assert result[0]["ingredients"] == [{"name": "Oats", "product_id": 1}]
