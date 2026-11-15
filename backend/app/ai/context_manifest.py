import hashlib
import json
from collections.abc import Iterable

from app.ai.schemas import ContextManifest, ManifestItem
from app.ai.validators import AIValidationError, assert_no_identifiers
from app.rules.classify import classify

# Only what recipe suggestions need: keeps the request under the provider's size limit.
NUTRIENTS = ("calories", "sodium_mg", "sugar_g", "sat_fat_g", "potassium_mg", "protein_g")


def _assert_no_product_identifiers(manifest: ContextManifest, products: list) -> None:
    """Reject any real sku/barcode/image_url value (or a bare id) inside manifest text."""
    texts = [
        t.lower()
        for t in [
            *manifest.restrictions,
            *(s for i in manifest.items for s in (i.name, i.category, *i.allergens, *i.diet_flags)),
        ]
    ]
    for product in products:
        for value in (product.sku, product.barcode, product.image_url):
            if value and any(str(value).lower() in t for t in texts):
                raise AIValidationError("product identifier found in manifest text")
        if str(product.id) in texts:
            raise AIValidationError("product id found in manifest text")


def _household_bucket(size: int | None):
    if size is None:
        return None
    return "1-2" if size <= 2 else "3-4" if size <= 4 else "5+"


def build_manifest(
    products: Iterable,
    restrictions: list[str],
    cart_quantities: dict[int, int] | None = None,
    household_size: int | None = None,
    focus_product_id: int | None = None,
    cuisine: str | None = None,
) -> tuple[ContextManifest, dict[int, int]]:
    """Build the AI-safe manifest. Returns (manifest, index -> real product_id).

    Keep the map server-side."""
    cart_quantities = cart_quantities or {}
    products = list(products)
    items, index_map = [], {}
    for index, product in enumerate(products):
        index_map[index] = product.id
        items.append(
            ManifestItem(
                index=index,
                name=product.name,
                category=product.category,
                status=classify(product, {"restrictions": restrictions})[0],
                in_cart_quantity=cart_quantities.get(product.id, 0),
                nutrition={
                    n: getattr(product, n)
                    for n in NUTRIENTS
                    if getattr(product, n, None) is not None
                },
                allergens=list(product.allergens or []),
                diet_flags=list(product.diet_flags or []),
            )
        )
    manifest = ContextManifest(
        restrictions=list(restrictions),
        household_size_bucket=_household_bucket(household_size),
        items=items,
        focus_index=next(
            (index for index, pid in index_map.items() if pid == focus_product_id), None
        ),
        cuisine=cuisine,
    )
    assert_no_identifiers(manifest.model_dump())
    _assert_no_product_identifiers(manifest, products)
    return manifest, index_map


def manifest_hash(manifest: ContextManifest) -> str:
    return hashlib.sha256(json.dumps(manifest.model_dump(), sort_keys=True).encode()).hexdigest()
