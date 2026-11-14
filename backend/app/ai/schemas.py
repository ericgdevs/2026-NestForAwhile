"""AI-facing payloads and output models.

`product_id` in AI output is the manifest index, never a real ID."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, StrictInt

Status = Literal["Approved", "Capped", "Restricted"]


class Strict(BaseModel):
    """Base for all AI-facing models: unknown fields (e.g. a status) are rejected."""

    model_config = ConfigDict(extra="forbid")


class ManifestItem(Strict):
    """One inventory item as the AI sees it.

    `status` is copied from rules.classify() and is read-only."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "index": 0,
                    "name": "Black beans",
                    "category": "Canned",
                    "status": "Approved",
                    "in_cart_quantity": 2,
                    "nutrition": {"sodium_mg": 120.0},
                    "allergens": [],
                    "diet_flags": ["vegan"],
                }
            ]
        },
    )

    index: StrictInt = Field(
        ge=0, description="Per-request item index; the real product ID never leaves the server."
    )
    name: str
    category: str
    status: Status  # always from rules.classify(); read-only for the AI
    in_cart_quantity: int = 0
    nutrition: dict[str, float] = {}
    allergens: list[str] = []
    diet_flags: list[str] = []


class ContextManifest(Strict):
    """AI-safe payload: restrictions, a household-size bucket and indexed items.

    Contains no identifiers."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "restrictions": ["Vegan"],
                    "household_size_bucket": "3-4",
                    "items": [
                        {
                            "index": 0,
                            "name": "Black beans",
                            "category": "Canned",
                            "status": "Approved",
                        }
                    ],
                }
            ]
        },
    )

    restrictions: list[str]
    household_size_bucket: Literal["1-2", "3-4", "5+"] | None = None
    items: list[ManifestItem]


class RecipeIngredient(Strict):
    """One recipe ingredient; `product_id` is a manifest index or null."""

    name: str
    product_id: StrictInt | None = Field(
        description="Manifest index of an in-stock item, or null for a pantry item."
    )


class Recipe(Strict):
    """A single recipe; title capped at 80 characters per the contract."""

    title: str = Field(max_length=80)
    ingredients: list[RecipeIngredient] = Field(min_length=1)
    steps: list[str] = Field(min_length=1)


class RecipeOutput(Strict):
    """Recipe suggestions (1-3).

    Mirrors contracts/ai-schemas.json `recipe_output`; `product_id` is a manifest index."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "recipes": [
                        {
                            "title": "Bean soup",
                            "ingredients": [{"name": "Black beans", "product_id": 0}],
                            "steps": ["Heat the beans."],
                        }
                    ]
                }
            ]
        },
    )

    recipes: list[Recipe] = Field(min_length=1, max_length=3)


class ExplanationOutput(Strict):
    """Short explanation of a rules-made recommendation.

    Mirrors `explanation_output`; may not carry a status."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"examples": [{"text": "Beans are high in fiber and fit your plan."}]},
    )

    text: str = Field(max_length=300)


class MissingIngredient(Strict):
    """One missing-ingredient suggestion."""

    product_id: StrictInt = Field(ge=0)
    reason: str


class MissingIngredientsOutput(Strict):
    """Suggested missing ingredients, by manifest index.

    Restricted items are rejected by the validator."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [{"items": [{"product_id": 3, "reason": "Adds flavor to the soup."}]}]
        },
    )

    items: list[MissingIngredient]


class Substitution(Strict):
    """One substitution suggestion."""

    original_product_id: StrictInt = Field(ge=0)
    substitute_product_id: StrictInt = Field(ge=0)
    reason: str


class SubstitutionsOutput(Strict):
    """Suggested substitutions by manifest index. The substitute may not be Restricted."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "substitutions": [
                        {
                            "original_product_id": 1,
                            "substitute_product_id": 0,
                            "reason": "Plant-based swap.",
                        }
                    ]
                }
            ]
        },
    )

    substitutions: list[Substitution]
