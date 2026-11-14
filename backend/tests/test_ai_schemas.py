import pytest
from pydantic import ValidationError

from app.ai.schemas import validate_recipe_output


def test_recipe_output_rejects_extra_fields_and_unknown_products():
    with pytest.raises(ValidationError):
        validate_recipe_output(
            {
                "recipes": [
                    {
                        "title": "Synthetic meal",
                        "ingredients": [{"name": "Mystery", "product_id": 99}],
                        "steps": ["Serve"],
                        "extra": True,
                    }
                ]
            },
            {1},
        )
    with pytest.raises(ValueError, match="unknown product"):
        validate_recipe_output(
            {
                "recipes": [
                    {
                        "title": "Synthetic meal",
                        "ingredients": [{"name": "Mystery", "product_id": 99}],
                        "steps": ["Serve"],
                    }
                ]
            },
            {1},
        )


def test_recipe_output_rejects_empty_or_malformed_payload():
    with pytest.raises(ValidationError):
        validate_recipe_output({"recipes": []}, {1})
    with pytest.raises(ValidationError):
        validate_recipe_output({"recipes": [{"title": "No ingredients"}]}, {1})
