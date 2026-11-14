import hashlib
import json
from collections.abc import Iterable

from app.ai.schemas import ContextManifest, ManifestItem
from app.ai.validators import assert_no_identifiers
from app.rules.classify import classify

NUTRIENTS = (
    "calories", "sodium_mg", "sugar_g", "added_sugar_g", "sat_fat_g", "fiber_g",
    "protein_g", "potassium_mg", "phosphorus_mg", "carbs_g",
)
_STATUS_LABEL = {0: "Approved", 1: "Capped", 2: "Restricted"}


def _household_bucket(size: int | None):
    if size is None:
        return None
    return "1-2" if size <= 2 else "3-4" if size <= 4 else "5+"


def build_manifest(
    products: Iterable,
    restrictions: list[str],
    cart_quantities: dict[int, int] | None = None,
    household_size: int | None = None,
) -> tuple[ContextManifest, dict[int, int]]:
    """Build the AI-safe manifest. Returns (manifest, index -> real product_id); keep the map server-side."""
    cart_quantities = cart_quantities or {}
    items, index_map = [], {}
    for index, product in enumerate(products):
        index_map[index] = product.id
        items.append(ManifestItem(
            index=index,
            name=product.name,
            category=product.category,
            status=_STATUS_LABEL[int(classify(product, restrictions).status)],
            in_cart_quantity=cart_quantities.get(product.id, 0),
            nutrition={n: getattr(product, n) for n in NUTRIENTS if getattr(product, n, None) is not None},
            allergens=list(product.allergens or []),
            diet_flags=list(product.diet_flags or []),
        ))
    manifest = ContextManifest(
        restrictions=list(restrictions), household_size_bucket=_household_bucket(household_size), items=items,
    )
    assert_no_identifiers(manifest.model_dump())
    return manifest, index_map


def manifest_hash(manifest: ContextManifest) -> str:
    return hashlib.sha256(json.dumps(manifest.model_dump(), sort_keys=True).encode()).hexdigest()
