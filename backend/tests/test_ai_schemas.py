import pytest

from app.ai.schemas import ContextManifest, ManifestItem
from app.ai.validators import AIValidationError, validate_ai_output

MANIFEST = ContextManifest(
    restrictions=[],
    items=[ManifestItem(index=1, name="Synthetic oats", category="Grain", status="Approved")],
)


def recipe(ingredient, **extra):
    body = {"title": "Synthetic meal", "ingredients": [ingredient], "steps": ["Serve"], **extra}
    return {"recipes": [body]}


def test_recipe_output_rejects_extra_fields_and_unknown_products():
    with pytest.raises(AIValidationError):
        payload = recipe({"name": "Mystery", "product_id": 1}, extra=True)
        validate_ai_output("recipes", payload, MANIFEST)
    with pytest.raises(AIValidationError, match="unknown index"):
        validate_ai_output("recipes", recipe({"name": "Mystery", "product_id": 99}), MANIFEST)


def test_recipe_output_rejects_empty_or_malformed_payload():
    with pytest.raises(AIValidationError):
        validate_ai_output("recipes", {"recipes": []}, MANIFEST)
    with pytest.raises(AIValidationError):
        validate_ai_output("recipes", {"recipes": [{"title": "No ingredients"}]}, MANIFEST)
