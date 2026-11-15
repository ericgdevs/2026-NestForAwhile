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
        ("Low Sodium", "sodium_mg", 141, 480),
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


from app.rules.classify import conditions_to_choices, household_label  # noqa: E402

NUT_CRACKER = {
    "sugar_g": 1,
    "sodium_mg": 100,
    "sat_fat_g": 1,
    "potassium_mg": 50,
    "allergens": ["contains_tree_nut"],
    "diet_flags": [],
}
ADULT = {"nickname": "Person 1", "restrictions": [], "allergies": []}
CHILD = {"nickname": "Little one", "restrictions": [], "allergies": ["Nut Allergy"]}
ALLERGIC_ADULT = {"nickname": "Person 1", "restrictions": [], "allergies": ["Nut Allergy"]}


def test_household_green_when_no_member_is_restricted():
    label = household_label(NUT_CRACKER, [ADULT, {**ADULT, "nickname": "Person 2"}])
    assert label["status"] == "Approved"
    assert label["not_for"] == [] and label["allergy_match"] is False


def test_household_yellow_when_some_members_are_restricted():
    label = household_label(NUT_CRACKER, [ADULT, CHILD])
    assert label["status"] == "Capped"
    assert label["not_for"] == [{"nickname": "Little one", "reason": "Nut Allergy"}]
    assert label["allergy_match"] is True


def test_household_red_when_every_member_is_restricted():
    assert household_label(NUT_CRACKER, [CHILD])["status"] == "Restricted"
    assert household_label(NUT_CRACKER, [ALLERGIC_ADULT, CHILD])["status"] == "Restricted"


def test_household_capped_guideline_makes_it_at_least_yellow():
    salty = {**NUT_CRACKER, "allergens": [], "sodium_mg": 300}
    member = {"nickname": "P1", "restrictions": ["Low Sodium"], "allergies": []}
    label = household_label(salty, [member])
    assert label["status"] == "Capped" and label["not_for"] == []


def test_household_without_members_is_never_approved():
    assert household_label(NUT_CRACKER, [])["status"] == "Capped"


def test_restriction_match_is_not_an_allergy_match():
    gluten = {**NUT_CRACKER, "allergens": [], "diet_flags": ["contains_gluten"]}
    member = {"nickname": "P1", "restrictions": ["Gluten Free"], "allergies": []}
    label = household_label(gluten, [member, ADULT])
    assert label["status"] == "Capped" and label["allergy_match"] is False


def test_conditions_map_to_choices_and_reject_unknown():
    assert conditions_to_choices(["E11", "N18"]) == [
        "Kidney Friendly",
        "Low Sodium",
        "Low Sugar",
    ]
    with pytest.raises(ValueError):
        conditions_to_choices(["Diabetes"])  # names are not codes


@pytest.mark.parametrize(
    ("sodium_mg", "status"),
    [(120, "Approved"), (140, "Approved"), (148, "Capped"), (479, "Capped"), (480, "Restricted")],
)
def test_low_sodium_uses_the_fda_low_and_high_definitions(sodium_mg, status):
    chips = product(sodium_mg=sodium_mg)  # "Potato chips, salted" is 148 mg per serving
    assert classify(chips, {"restrictions": ["Low Sodium"]})[0] == status
