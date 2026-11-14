import json
from types import SimpleNamespace

import pytest

from app.ai.context_manifest import build_manifest, manifest_hash
from app.ai.validators import AIValidationError
from app.rules.classify import classify


def product(pid, name="Beans", **kw):
    base = dict(id=pid, sku=f"SKU{pid}", barcode="0123456789012", name=name, category="Canned",
                image_url="https://img.test/a.png", sodium_mg=100.0, calories=None,
                allergens=[], diet_flags=["vegan"], ingredients_text="beans")
    return SimpleNamespace(**{**base, **kw})


PRODUCTS = [product(501), product(502, "Almond milk", allergens=["tree nuts"], diet_flags=[])]


def test_strips_identifiers_and_maps_indexes():
    manifest, index_map = build_manifest(PRODUCTS, ["Nut Allergy"], {501: 2}, household_size=4)
    dumped = json.dumps(manifest.model_dump())
    for leak in ("SKU501", "0123456789012", "img.test", "501", "502"):
        assert leak not in dumped
    assert index_map == {0: 501, 1: 502}
    assert manifest.items[0].in_cart_quantity == 2
    assert manifest.household_size_bucket == "3-4"
    assert "calories" not in manifest.items[0].nutrition


def test_status_comes_from_classify():
    manifest, _ = build_manifest(PRODUCTS, ["Nut Allergy"])
    assert [i.status for i in manifest.items] == [classify(p, ["Nut Allergy"]).status.name.title() for p in PRODUCTS]
    assert manifest.items[1].status == "Restricted"


def test_identifier_in_product_name_is_blocked():
    with pytest.raises(AIValidationError):
        build_manifest([product(1, "Call 555-123-4567")], [])


def test_hash_is_stable_and_content_sensitive():
    a, _ = build_manifest(PRODUCTS, ["Nut Allergy"])
    b, _ = build_manifest(PRODUCTS, ["Nut Allergy"])
    c, _ = build_manifest(PRODUCTS, ["Nut Allergy"], {501: 1})
    assert manifest_hash(a) == manifest_hash(b) != manifest_hash(c)
