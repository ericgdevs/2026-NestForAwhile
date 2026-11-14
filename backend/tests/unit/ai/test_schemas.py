import pytest
from pydantic import ValidationError

from app.ai.schemas import ExplanationOutput, RecipeOutput

GOOD = {"recipes": [{"title": "Soup", "ingredients": [{"name": "Beans", "product_id": 0}], "steps": ["Heat"]}]}


def test_valid_recipe_output():
    assert RecipeOutput.model_validate(GOOD).recipes[0].title == "Soup"


@pytest.mark.parametrize("bad", [
    {"recipes": []},
    {"recipes": GOOD["recipes"], "status": "Approved"},
    {"recipes": [{**GOOD["recipes"][0], "status": "Approved"}]},
])
def test_recipe_output_rejects_empty_and_extra_fields(bad):
    with pytest.raises(ValidationError):
        RecipeOutput.model_validate(bad)


def test_explanation_length_cap():
    with pytest.raises(ValidationError):
        ExplanationOutput(text="x" * 301)
