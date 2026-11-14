from types import SimpleNamespace

import pytest

from app.rules.classify import Status, classify
from app.rules.tiers import tier_for


def product(**kw):
    base = dict(allergens=[], diet_flags=["is_vegan"], ingredients_text="oats", sodium_mg=50, sugar_g=1,
                added_sugar_g=0, sat_fat_g=0.5, potassium_mg=50, phosphorus_mg=20)
    return SimpleNamespace(**{**base, **kw})


@pytest.mark.parametrize("restrictions,changes,expected", [
    ([], {}, Status.APPROVED),
    (["Low Sodium"], {"sodium_mg": 200}, Status.CAPPED),
    (["Low Sodium"], {"sodium_mg": 500}, Status.RESTRICTED),
    (["Low Sugar"], {"sugar_g": 7}, Status.CAPPED),
    (["Kidney Friendly"], {"potassium_mg": 450}, Status.RESTRICTED),
    (["Nut Allergy"], {"allergens": ["Peanuts"]}, Status.RESTRICTED),
    (["Vegan"], {"diet_flags": ["contains_dairy"]}, Status.RESTRICTED),
    (["Low Sodium"], {"sodium_mg": None}, Status.CAPPED),
    (["Gluten Free"], {"allergens": [], "diet_flags": [], "ingredients_text": None}, Status.CAPPED),
    # overlapping: strictest wins (capped for sugar, restricted for sodium)
    (["Low Sugar", "Low Sodium"], {"sugar_g": 7, "sodium_mg": 500}, Status.RESTRICTED),
])
def test_classify(restrictions, changes, expected):
    assert classify(product(**changes), restrictions).status == expected


def test_missing_data_reason_is_plain_language():
    result = classify(product(sodium_mg=None), ["Low Sodium"])
    assert "ask a volunteer" in result.reason


def test_tier_strictest_wins():
    assert tier_for([]) == 1
    assert tier_for(["Vegan"]) == 2
    assert tier_for(["Vegan", "Low Sugar"]) == 3
    assert tier_for(["Low Sugar", "Kidney Friendly"]) == 4
