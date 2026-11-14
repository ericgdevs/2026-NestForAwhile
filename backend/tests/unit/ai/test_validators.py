import pytest

from app.ai.schemas import ContextManifest, ManifestItem
from app.ai.validators import AIValidationError, assert_no_identifiers, validate_ai_output

MANIFEST = ContextManifest(restrictions=["Vegan"], items=[
    ManifestItem(index=0, name="Beans", category="Canned", status="Approved"),
    ManifestItem(index=1, name="Cheese", category="Dairy", status="Restricted"),
])


def recipe(product_id):
    return {"recipes": [{"title": "T", "ingredients": [{"name": "x", "product_id": product_id}], "steps": ["go"]}]}


def test_valid_recipe_and_pantry_item_pass():
    assert validate_ai_output("recipes", recipe(0), MANIFEST)
    assert validate_ai_output("recipes", recipe(None), MANIFEST)


def test_accepts_json_string():
    import json
    assert validate_ai_output("recipes", json.dumps(recipe(0)), MANIFEST)


@pytest.mark.parametrize("raw", ["not json", recipe(99), recipe(1)])
def test_rejects_malformed_unknown_index_and_restricted(raw):
    with pytest.raises(AIValidationError):
        validate_ai_output("recipes", raw, MANIFEST)


def test_rejects_status_override():
    data = recipe(0)
    data["recipes"][0]["status"] = "Approved"
    with pytest.raises(AIValidationError, match="status"):
        validate_ai_output("recipes", data, MANIFEST)


def test_rejects_identifier_leak_in_output():
    data = {"text": "Email jane@example.test for help"}
    with pytest.raises(AIValidationError, match="identifier"):
        validate_ai_output("explain", data, MANIFEST)


def test_substitution_may_replace_restricted_but_not_suggest_one():
    ok = {"substitutions": [{"original_product_id": 1, "substitute_product_id": 0, "reason": "vegan"}]}
    assert validate_ai_output("substitutions", ok, MANIFEST)
    bad = {"substitutions": [{"original_product_id": 0, "substitute_product_id": 1, "reason": "x"}]}
    with pytest.raises(AIValidationError, match="restricted"):
        validate_ai_output("substitutions", bad, MANIFEST)


def test_unsupported_task():
    with pytest.raises(AIValidationError):
        validate_ai_output("chat", {}, MANIFEST)


@pytest.mark.parametrize("payload", [
    {"sku": "A1"}, {"items": [{"barcode": "x"}]}, {"image_url": "x"},
    {"t": "a@b.co"}, {"t": "call 555-123-4567"}, {"t": "0123456789012"}, {"t": "https://x.test/i.png"},
])
def test_assert_no_identifiers_rejects(payload):
    with pytest.raises(AIValidationError):
        assert_no_identifiers(payload)


def test_assert_no_identifiers_allows_plain_text():
    assert_no_identifiers({"name": "Black beans, 15 oz", "n": 12345678})
