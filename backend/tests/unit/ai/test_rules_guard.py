from pathlib import Path
from types import SimpleNamespace

import pytest

import app.ai.rules_guard as guard_module
from app.ai.context_manifest import build_manifest, manifest_hash
from app.ai.orchestrator import AIResult
from app.ai.rules_guard import apply_rules_guard
from app.ai.schemas import ExplanationOutput, MissingIngredientsOutput, RecipeOutput, SubstitutionsOutput

RESTRICTIONS = ["Nut Allergy"]


def product(pid, name, **kw):
    base = dict(id=pid, sku=f"S{pid}", barcode="0123456789012", category="Canned", image_url=None, sodium_mg=100.0,
                allergens=[], diet_flags=["vegan"], ingredients_text="x")
    return SimpleNamespace(**{**base, "name": name, **kw})


BEANS = product(501, "Beans")
RICE = product(503, "Rice")
ALMOND = product(502, "Almond milk", allergens=["tree nuts"], diet_flags=["contains_tree_nut"])
PRODUCTS = [BEANS, ALMOND, RICE]  # indexes 0, 1, 2
IN_STOCK = {501, 502, 503}


def guard(output, products=PRODUCTS, in_stock=IN_STOCK):
    """Manifest is built from PRODUCTS (what the AI saw); `products` is the inventory at guard time."""
    manifest, index_map = build_manifest(PRODUCTS, RESTRICTIONS)
    result = AIResult(output, manifest_hash(manifest), index_map, "fake")
    return apply_rules_guard(result, manifest, products, RESTRICTIONS, in_stock)


def recipes(*index_lists):
    return RecipeOutput(recipes=[
        {"title": f"R{n}", "ingredients": [{"name": "x", "product_id": i} for i in idxs], "steps": ["go"]}
        for n, idxs in enumerate(index_lists)
    ])


def titles(result):
    return [r.title for r in result.output.recipes]


def test_valid_recommendation_passes_through_unchanged():
    output = recipes([0, 2], [None])
    result = guard(output)
    assert result.output == output and result.dropped == []


def test_restricted_suggestion_is_dropped():
    result = guard(recipes([0], [0, 1]))
    assert titles(result) == ["R0"] and result.dropped == [("restricted", 1)]


def test_index_out_of_range_is_dropped():
    result = guard(recipes([0], [7]))
    assert titles(result) == ["R0"] and result.dropped == [("invalid_index", 7)]


def test_negative_index_is_dropped():
    assert guard(recipes([-1])).dropped == [("invalid_index", -1)]


def test_stale_index_when_product_left_inventory():
    result = guard(recipes([0], [2]), products=[BEANS, ALMOND])
    assert titles(result) == ["R0"] and result.dropped == [("stale_index", 2)]


def test_unavailable_when_out_of_stock():
    result = guard(recipes([0], [2]), in_stock={501, 502})
    assert titles(result) == ["R0"] and result.dropped == [("unavailable", 2)]


def test_classification_mismatch_when_inventory_changed_since_manifest():
    changed = product(503, "Rice", allergens=None, diet_flags=None, ingredients_text=None)  # now has no exclusion data -> Capped, AI saw Approved
    result = guard(recipes([0], [2]), products=[BEANS, ALMOND, changed])
    assert titles(result) == ["R0"] and result.dropped == [("classification_mismatch", 2)]


def test_product_newly_restricted_is_dropped_as_restricted():
    nutty = product(503, "Rice", allergens=["peanuts"], diet_flags=["contains_peanut"])
    assert guard(recipes([2]), products=[BEANS, ALMOND, nutty]).dropped == [("restricted", 2)]


def test_all_recipes_filtered_gives_empty_list_not_error():
    result = guard(recipes([1], [9]))
    assert result.output.recipes == [] and len(result.dropped) == 2


def test_empty_recommendation_lists_pass_through():
    empty_recipes = RecipeOutput.model_construct(recipes=[])
    assert guard(empty_recipes).output.recipes == []
    assert guard(MissingIngredientsOutput(items=[])).output.items == []
    assert guard(SubstitutionsOutput(substitutions=[])).output.substitutions == []


def test_missing_ingredients_filtered():
    output = MissingIngredientsOutput(items=[{"product_id": 0, "reason": "a"}, {"product_id": 1, "reason": "b"}])
    result = guard(output)
    assert [i.product_id for i in result.output.items] == [0] and result.dropped == [("restricted", 1)]


def test_substitution_original_may_be_restricted_but_substitute_may_not():
    output = SubstitutionsOutput(substitutions=[
        {"original_product_id": 1, "substitute_product_id": 0, "reason": "ok"},
        {"original_product_id": 0, "substitute_product_id": 1, "reason": "bad"},
    ])
    result = guard(output)
    assert [s.substitute_product_id for s in result.output.substitutions] == [0]
    assert result.dropped == [("restricted", 1)]


def test_explanation_passes_through():
    output = ExplanationOutput(text="Rules marked this Restricted.")
    assert guard(output).output == output


def test_input_is_not_mutated():
    output = recipes([0], [1])
    guard(output)
    assert len(output.recipes) == 2


def test_unsupported_output_type_raises():
    with pytest.raises(TypeError):
        guard({"recipes": []})


def test_guard_is_deterministic_and_makes_no_external_calls():
    source = Path(guard_module.__file__).read_text().lower()
    for forbidden in ("provider", "httpx", "requests", "groq", "ollama", "get_settings"):
        assert forbidden not in source
    assert guard(recipes([0], [1])) == guard(recipes([0], [1]))
