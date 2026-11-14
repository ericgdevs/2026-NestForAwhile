from app.rules.classify import RESTRICTED
from app.services.recipe_guard import guard_recipes


def test_recipe_guard_drops_missing_and_restricted_ingredients():
    recipes = [
        {"ingredients": [{"product_id": 1}]},
        {"ingredients": [{"product_id": 2}]},
    ]
    products = {
        1: {"diet_flags": ["contains_dairy"], "allergens": []},
        2: {"diet_flags": [], "allergens": []},
    }
    guarded = guard_recipes(
        recipes,
        products,
        {"restrictions": ["Dairy Free"], "allergies": []},
        {1, 2},
    )
    assert guarded == [recipes[1]]
    assert RESTRICTED == "Restricted"
