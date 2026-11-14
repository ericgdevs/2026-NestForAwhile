"""AI-facing payloads and output models. `product_id` in AI output is the manifest index, never a real ID."""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Status = Literal["Approved", "Capped", "Restricted"]


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ManifestItem(Strict):
    index: int
    name: str
    category: str
    status: Status  # always from rules.classify(); read-only for the AI
    in_cart_quantity: int = 0
    nutrition: dict[str, float] = {}
    allergens: list[str] = []
    diet_flags: list[str] = []


class ContextManifest(Strict):
    restrictions: list[str]
    household_size_bucket: Literal["1-2", "3-4", "5+"] | None = None
    items: list[ManifestItem]


class RecipeIngredient(Strict):
    name: str
    product_id: int | None


class Recipe(Strict):
    title: str = Field(max_length=80)
    ingredients: list[RecipeIngredient] = Field(min_length=1)
    steps: list[str] = Field(min_length=1)


class RecipeOutput(Strict):
    recipes: list[Recipe] = Field(min_length=1, max_length=3)


class ExplanationOutput(Strict):
    text: str = Field(max_length=300)


class MissingIngredient(Strict):
    product_id: int
    reason: str


class MissingIngredientsOutput(Strict):
    items: list[MissingIngredient]


class Substitution(Strict):
    original_product_id: int
    substitute_product_id: int
    reason: str


class SubstitutionsOutput(Strict):
    substitutions: list[Substitution]
