import pytest

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


def _guard(ingredients, restrictions=()):
    recipe = {"ingredients": ingredients}
    products = {
        1: {"diet_flags": [], "allergens": []},
        2: {"diet_flags": ["contains_dairy"], "allergens": []},
    }
    profile = {"restrictions": [], "allergies": list(restrictions)}
    return guard_recipes([recipe], products, profile, {1, 2}) == [recipe]


def test_allowlisted_null_id_basics_keep_the_recipe():
    names = ["Water", "ice", "Black pepper", "freshly ground black pepper", "Fresh basil",
             "ground cumin", "Lemon juice", "chili powder", "Garlic powder", "vinegar"]  # fmt: skip
    for name in names:
        assert _guard([{"name": "Rice", "product_id": 1}, {"name": name, "product_id": None}])


@pytest.mark.parametrize(
    "name", ["Salt", "sugar", "Honey", "olive oil", "soy sauce", "butter", "milk",
             "salt and black pepper", "black pepper, salt", "Unicorn dust", "", None]
)  # fmt: skip
def test_other_null_id_ingredients_still_drop_the_recipe(name):
    assert not _guard([{"name": "Rice", "product_id": 1}, {"name": name, "product_id": None}])


def test_restricted_or_unavailable_product_still_drops_with_basics():
    water = {"name": "Water", "product_id": None}
    assert not _guard([water, {"name": "Cheese", "product_id": 2}], ["Dairy Free"])
    assert not _guard([water, {"name": "Ghost", "product_id": 99}])
