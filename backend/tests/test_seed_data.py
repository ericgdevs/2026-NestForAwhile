import json
from datetime import date

import pytest
from cryptography.fernet import Fernet
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from app.auth import email_lookup_hash
from app.db import Base
from app.models import (
    Client,
    DietaryProfile,
    HouseholdMember,
    InventoryLot,
    Product,
    User,
)
from app.rules.classify import APPROVED, CAPPED, CONDITIONS, RESTRICTED, RULES, classify
from app.rules.tiers import DIETARY_TIER_IDS
from app.services.nutrition import household_choices
from seed.load import PRODUCT_SEEDS, SYNTHETIC_PASSWORD, seed_catalog, seed_users

# email -> (expected Dietary_Tier_ID, household size, enrollment status)
PERSONAS = {
    "client.active@example.test": (9, 2, "Active"),  # child nut allergy
    "client.pending@example.test": (10, 6, "Pending"),  # large household
    "client.diabetes.htn@example.test": (4, 1, "Active"),
    "client.ckd.htn@example.test": (5, 2, "Active"),
    "client.diabetes.ckd@example.test": (5, 1, "Active"),  # potassium conflict
}
RULE_NUTRIENTS = ("sodium_mg", "sugar_g", "sat_fat_g", "potassium_mg")
EXTRA_NUTRIENTS = ("calories", "protein_g", "fiber_g", "carbs_g", "phosphorus_mg")


@pytest.fixture
def database(monkeypatch):
    monkeypatch.setenv("FIELD_ENCRYPTION_KEY", Fernet.generate_key().decode())
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        seed_users(session)
        seed_catalog(session)
        yield session


def _client(database, email):
    user = database.scalar(select(User).where(User.email_hash == email_lookup_hash(email)))
    return database.get(Client, user.id)


def test_every_product_has_nutrients_allergen_tags_bin_and_stock(database):
    products = database.scalars(select(Product)).all()
    assert len(products) >= 100
    assert len({p.barcode for p in products}) == len(products)
    for product in products:
        legacy = product.sku in {seed["sku"] for seed in PRODUCT_SEEDS}  # kept unchanged
        wanted = RULE_NUTRIENTS if legacy else RULE_NUTRIENTS + EXTRA_NUTRIENTS
        assert all(getattr(product, n) is not None for n in wanted), product.sku
        assert product.allergens is not None and product.diet_flags is not None, product.sku
        lots = product.inventory_lots
        assert sum(lot.quantity for lot in lots) > 0, product.sku
        assert all(lot.aisle and lot.shelf and lot.bin for lot in lots), product.sku
        assert all(lot.expiration_date >= date.today() for lot in lots), product.sku
    assert {p.category for p in products} >= {
        "Produce", "Proteins", "Dairy", "Grains", "Canned Goods", "Snacks", "Beverages",
    }  # fmt: skip


def test_every_rule_fires_on_at_least_one_product(database):
    products = database.scalars(select(Product)).all()
    for rule in RULES:
        profile = {"restrictions": [rule]}
        statuses = {classify(p, profile)[0] for p in products}
        assert {CAPPED, RESTRICTED} & statuses, rule
    tags = {t for p in products for t in p.allergens}
    assert {"contains_dairy", "contains_egg", "contains_peanut", "contains_tree_nut"} <= tags
    assert {"contains_fish", "contains_soy"} <= tags
    assert any(p.sodium_mg > 960 for p in products)
    assert any(p.potassium_mg > 600 for p in products)


def test_existing_skus_are_unchanged(database):
    for seed in PRODUCT_SEEDS:
        product = database.scalar(select(Product).where(Product.sku == seed["sku"]))
        assert product.name == seed["name"] and product.barcode == seed["barcode"]


def test_matrix_covers_every_tier_and_cites_a_source():
    assert set(RULES) == set(DIETARY_TIER_IDS)
    assert all(rule["source"] for rule in RULES.values())
    assert all(entry["source"] for entry in CONDITIONS.values())


def test_five_personas_have_expected_households_conditions_and_tiers(database):
    for email, (tier, size, status) in PERSONAS.items():
        client = _client(database, email)
        assert client.Dietary_Tier_ID == tier, email
        assert client.Household_Size == size == len(client.members), email
        assert client.Client_Enrollment_Status == status, email
    statuses = [s for _, _, s in PERSONAS.values()]
    assert statuses.count("Pending") == 1
    both = household_choices(_client(database, "client.diabetes.ckd@example.test"))
    assert {"Low Sugar", "Kidney Friendly"} <= set(both["restrictions"])
    htn = household_choices(_client(database, "client.ckd.htn@example.test"))
    assert {"Kidney Friendly", "Low Sodium", "Heart Healthy"} <= set(htn["restrictions"])


def test_every_persona_has_a_recipe_sized_set_of_approved_in_stock_products(database):
    in_stock = {
        lot.product_id for lot in database.scalars(select(InventoryLot)) if lot.quantity > 0
    }
    products = [p for p in database.scalars(select(Product)) if p.id in in_stock]
    for email in PERSONAS:
        profile = household_choices(_client(database, email))
        approved = [p for p in products if classify(p, profile)[0] == APPROVED]
        categories = {p.category for p in approved}
        assert len(approved) >= 12, (email, len(approved))
        assert len(categories) >= 4, (email, categories)


def test_seeding_twice_adds_no_duplicates_and_keeps_passwords(database):
    def counts():
        return [
            database.scalar(select(func.count()).select_from(model))
            for model in (User, Client, DietaryProfile, HouseholdMember, Product, InventoryLot)
        ]

    before = counts()
    hashes = dict(database.execute(select(User.email_hash, User.password_hash)).all())
    seed_users(database)
    seed_catalog(database)
    assert counts() == before
    assert dict(database.execute(select(User.email_hash, User.password_hash)).all()) == hashes
    assert SYNTHETIC_PASSWORD == "demo-password"


def test_seed_heals_a_database_with_the_old_four_product_seed(database):
    active = _client(database, "client.active@example.test")
    little = next(m for m in active.members if m.nickname == "Little one")
    database.delete(little)  # old DB: client.active only had "Person 1"
    active.Household_Size, active.Dietary_Tier_ID = 1, 3
    old_skus = [seed["sku"] for seed in PRODUCT_SEEDS]
    extra = database.scalars(select(Product).where(Product.sku.not_in(old_skus))).all()
    for product in extra:  # old DB: only the original four products
        for lot in product.inventory_lots:
            database.delete(lot)
        database.delete(product)
    database.commit()
    database.expire_all()
    active = _client(database, "client.active@example.test")
    assert [m.nickname for m in active.members] == ["Person 1"]
    assert database.scalar(select(func.count()).select_from(Product)) == 4

    seed_users(database)
    seed_catalog(database)
    database.expire_all()

    active = _client(database, "client.active@example.test")
    assert [m.nickname for m in active.members] == ["Person 1", "Little one"]
    little = active.members[1]
    assert json.loads(little.allergies) == ["Nut Allergy"]
    assert active.Household_Size == 2 and active.Dietary_Tier_ID == 9
    profile = database.get(DietaryProfile, active.user_id)
    assert json.loads(profile.allergies) == ["Nut Allergy"]
    assert database.scalar(select(func.count()).select_from(Product)) >= 100
