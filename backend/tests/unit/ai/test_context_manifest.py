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


PRODUCTS = [product(501), product(502, "Almond milk", allergens=["tree nuts"], diet_flags=["contains_tree_nut"])]


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
    assert [i.status for i in manifest.items] == [classify(p, {"restrictions": ["Nut Allergy"]})[0] for p in PRODUCTS]
    assert manifest.items[1].status == "Restricted"


def test_identifier_in_product_name_is_blocked():
    with pytest.raises(AIValidationError):
        build_manifest([product(1, "Call 555-123-4567")], [])


def test_hash_is_stable_and_content_sensitive():
    a, _ = build_manifest(PRODUCTS, ["Nut Allergy"])
    b, _ = build_manifest(PRODUCTS, ["Nut Allergy"])
    c, _ = build_manifest(PRODUCTS, ["Nut Allergy"], {501: 1})
    assert manifest_hash(a) == manifest_hash(b) != manifest_hash(c)


@pytest.mark.parametrize("field, value", [
    ("name", "Beans SKU501"), ("category", "https://img.test/a.png"), ("diet_flags", ["0123456789012"]),
])
def test_real_product_values_in_text_are_blocked(field, value):
    with pytest.raises(AIValidationError):
        build_manifest([product(501, **{field: value})], [])


def test_bare_product_id_as_text_is_blocked():
    with pytest.raises(AIValidationError):
        build_manifest([product(501, name="501")], [])


@pytest.mark.parametrize("name", ["Contact jane@example.test", "Call 555-123-4567", "Code 0123456789012"])
def test_email_phone_barcode_patterns_in_names_are_blocked(name):
    with pytest.raises(AIValidationError):
        build_manifest([product(1, name=name)], [])


def test_manifest_has_no_identifier_fields():
    manifest, _ = build_manifest(PRODUCTS, [])
    keys = set(json.dumps(manifest.model_dump()).replace("}", ",").split('"')[1::2])
    assert not keys & {"id", "sku", "barcode", "image_url", "email", "phone", "client_id"}
