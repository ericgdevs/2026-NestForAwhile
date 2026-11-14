import pytest
from pydantic import ValidationError

from app.ai.schemas import (
    ContextManifest,
    ExplanationOutput,
    ManifestItem,
    MissingIngredientsOutput,
    RecipeOutput,
    SubstitutionsOutput,
)

GOOD = {
    "recipes": [
        {"title": "Soup", "ingredients": [{"name": "Beans", "product_id": 0}], "steps": ["Heat"]}
    ]
}


def test_valid_recipe_output():
    assert RecipeOutput.model_validate(GOOD).recipes[0].title == "Soup"


@pytest.mark.parametrize(
    "bad",
    [
        {"recipes": []},
        {"recipes": GOOD["recipes"], "status": "Approved"},
        {"recipes": [{**GOOD["recipes"][0], "status": "Approved"}]},
    ],
)
def test_recipe_output_rejects_empty_and_extra_fields(bad):
    with pytest.raises(ValidationError):
        RecipeOutput.model_validate(bad)


def test_explanation_length_cap():
    with pytest.raises(ValidationError):
        ExplanationOutput(text="x" * 301)


@pytest.mark.parametrize(
    "model",
    [
        ContextManifest,
        ManifestItem,
        RecipeOutput,
        ExplanationOutput,
        MissingIngredientsOutput,
        SubstitutionsOutput,
    ],
)
def test_documented_with_valid_examples(model):
    assert model.__doc__
    for example in model.model_json_schema()["examples"]:
        model.model_validate(example)


def test_manifest_item_rejects_ai_style_status_value():
    with pytest.raises(ValidationError):
        ManifestItem(index=0, name="x", category="y", status="Safe")


def test_index_is_strict_int():
    with pytest.raises(ValidationError):
        ManifestItem(index="0", name="x", category="y", status="Approved")
