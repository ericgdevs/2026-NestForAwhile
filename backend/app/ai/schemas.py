from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class Ingredient(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    product_id: int | None


class Recipe(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(max_length=80)
    ingredients: list[Ingredient] = Field(min_length=1)
    steps: list[str] = Field(min_length=1)


class RecipeOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    recipes: list[Recipe] = Field(min_length=1, max_length=3)


def validate_recipe_output(payload: object, product_ids: set[int]) -> RecipeOutput:
    output = RecipeOutput.model_validate(payload)
    unknown = {
        ingredient.product_id
        for recipe in output.recipes
        for ingredient in recipe.ingredients
        if ingredient.product_id is None or ingredient.product_id not in product_ids
    }
    if unknown:
        raise ValueError(f"Recipe contains unknown product IDs: {sorted(unknown)}")
    return output
