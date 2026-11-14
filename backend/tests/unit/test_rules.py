import pytest

from app.rules.classify import CAPPED, RESTRICTED, classify
from app.rules.tiers import dietary_tier_id


def product(**overrides):
    value = {
        "sugar_g": 4,
        "sodium_mg": 100,
        "sat_fat_g": 1,
        "potassium_mg": 100,
        "diet_flags": set(),
        "allergens": set(),
    }
    value.update(overrides)
    return value


@pytest.mark.parametrize(
    ("restriction", "field", "capped", "restricted"),
    [
        ("Low Sugar", "sugar_g", 13, 25),
        ("Low Sodium", "sodium_mg", 481, 961),
        ("Heart Healthy", "sat_fat_g", 5, 9),
        ("Kidney Friendly", "potassium_mg", 301, 601),
    ],
)
def test_nutrient_thresholds(restriction, field, capped, restricted):
    assert classify(product(**{field: capped}), {"restrictions": [restriction]})[0] == CAPPED
    assert (
        classify(product(**{field: restricted}), {"restrictions": [restriction]})[0] == RESTRICTED
    )


@pytest.mark.parametrize(
    ("restriction", "flag"),
    [
        ("Vegetarian", "contains_meat"),
        ("Vegan", "contains_dairy"),
        ("Gluten Free", "contains_gluten"),
        ("Nut Allergy", "contains_tree_nut"),
        ("Dairy Free", "contains_dairy"),
    ],
)
def test_exclusions_are_restricted(restriction, flag):
    assert classify(product(diet_flags={flag}), {"restrictions": [restriction]})[0] == RESTRICTED


def test_missing_relevant_data_is_capped():
    assert (
        classify({"diet_flags": None, "allergens": None}, {"restrictions": ["Vegan"]})[0] == CAPPED
    )


def test_tier_mapping_uses_strictest_selected_restriction():
    assert dietary_tier_id([]) == 1
    assert dietary_tier_id(["Low Sugar", "Dairy Free"]) == 10


def test_unknown_dietary_option_is_rejected():
    with pytest.raises(ValueError):
        dietary_tier_id(["Unknown"])
