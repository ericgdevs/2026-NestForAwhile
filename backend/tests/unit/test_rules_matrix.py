import pytest

from app.rules.matrix import load_matrix, restrictions_for_conditions

SPEC_RESTRICTIONS = {"Low Sugar", "Low Sodium", "Heart Healthy", "Kidney Friendly", "Vegetarian",
                     "Vegan", "Gluten Free", "Nut Allergy", "Dairy Free"}


def test_matrix_has_every_spec_restriction_and_is_marked_synthetic():
    matrix = load_matrix()
    assert set(matrix["restrictions"]) == SPEC_RESTRICTIONS
    assert matrix["synthetic_placeholder"] is True


def test_limits_are_ordered():
    for rule in load_matrix()["restrictions"].values():
        for limit in rule.get("limits", []):
            assert limit["capped_above"] < limit["restricted_above"]


def test_overlapping_conditions_combine_without_duplicates():
    assert restrictions_for_conditions(["hypertension", "ckd"]) == ["Low Sodium", "Heart Healthy", "Kidney Friendly"]


def test_unknown_condition_rejected():
    with pytest.raises(KeyError):
        restrictions_for_conditions(["flu"])
