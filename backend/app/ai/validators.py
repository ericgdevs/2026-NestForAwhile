import json
import re

from pydantic import ValidationError

from app.ai.schemas import (
    ContextManifest,
    ExplanationOutput,
    MissingIngredientsOutput,
    RecipeOutput,
    SubstitutionsOutput,
)


class AIValidationError(ValueError):
    pass


FORBIDDEN_KEYS = {
    "id",
    "sku",
    "barcode",
    "image_url",
    "email",
    "phone",
    "client_id",
    "user_id",
    "username",
    "first_name",
    "last_name",
}
# Any key containing one of these is treated as an attempt to set or change a status/classification.
STATUS_KEY_PARTS = (
    "status",
    "tier",
    "classif",
    "verdict",
    "override",
    "approved",
    "capped",
    "restricted",
)
IDENTIFIER_PATTERNS = [
    re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"),
    re.compile(r"https?://|www\.", re.I),
    re.compile(r"\+?\d[\d\s().-]{8,}\d"),
    re.compile(r"\d{8,}"),
    re.compile(r"\bsku\b[\s:#-]*\w*\d", re.I),
]
TASK_MODELS = {
    "explain": ExplanationOutput,
    "recipes": RecipeOutput,
    "missing_ingredients": MissingIngredientsOutput,
    "substitutions": SubstitutionsOutput,
}


def _walk(value, path=""):
    if isinstance(value, dict):
        for key, child in value.items():
            yield f"{path}/{key}", key, None
            yield from _walk(child, f"{path}/{key}")
    elif isinstance(value, list):
        for i, child in enumerate(value):
            yield from _walk(child, f"{path}/{i}")
    elif isinstance(value, str):
        yield path, None, value


def assert_no_identifiers(payload) -> None:
    """Reject identifier keys and identifier-looking strings.

    Covers email, URL, phone and barcode/SKU digits."""
    for path, key, text in _walk(payload):
        if key is not None and key.lower() in FORBIDDEN_KEYS:
            raise AIValidationError(f"identifier field at {path}")
        if text is not None and any(p.search(text) for p in IDENTIFIER_PATTERNS):
            raise AIValidationError(f"identifier-like value at {path}")


def _assert_no_status_override(raw) -> None:
    for path, key, _ in _walk(raw):
        if key is not None and any(
            part in re.sub(r"[^a-z]", "", key.lower()) for part in STATUS_KEY_PARTS
        ):
            raise AIValidationError(f"AI may not set or change status ({path})")


def _referenced_indexes(output) -> list[tuple[int, bool]]:
    """(index, may_be_restricted) for every manifest index the output uses."""
    if isinstance(output, RecipeOutput):
        return [
            (i.product_id, False)
            for r in output.recipes
            for i in r.ingredients
            if i.product_id is not None
        ]
    if isinstance(output, MissingIngredientsOutput):
        return [(i.product_id, False) for i in output.items]
    if isinstance(output, SubstitutionsOutput):
        return [
            r
            for s in output.substitutions
            for r in ((s.original_product_id, True), (s.substitute_product_id, False))
        ]
    return []


def validate_ai_output(task: str, raw: str | dict, manifest: ContextManifest):
    """Parse AI output for a task and enforce the rules-first guarantees.

    Returns the typed output."""
    if task not in TASK_MODELS:
        raise AIValidationError(f"unsupported AI task: {task}")
    if not isinstance(raw, str | dict):
        raise AIValidationError("AI output must be a JSON string or object")
    try:
        data = json.loads(raw) if isinstance(raw, str) else raw
    except json.JSONDecodeError as exc:
        raise AIValidationError("malformed JSON") from exc
    if not isinstance(data, dict):
        raise AIValidationError("AI output must be a JSON object")
    _assert_no_status_override(data)
    try:
        output = TASK_MODELS[task].model_validate(data)
    except ValidationError as exc:
        raise AIValidationError(f"schema violation: {exc.error_count()} error(s)") from exc
    assert_no_identifiers(data)
    status_by_index = {item.index: item.status for item in manifest.items}
    for index, may_be_restricted in _referenced_indexes(output):
        if index not in status_by_index:
            raise AIValidationError(f"unknown index {index}")
        if status_by_index[index] == "Restricted" and not may_be_restricted:
            raise AIValidationError(f"restricted item {index} suggested")
    return output
