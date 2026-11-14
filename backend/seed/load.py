from __future__ import annotations

import json
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import Role, email_lookup_hash, hash_password
from app.models import (
    Client,
    DietaryProfile,
    Donor,
    Grant,
    InventoryLot,
    Product,
    User,
)
from app.rules.tiers import dietary_tier_id

SYNTHETIC_PASSWORD = "demo-password"

USER_SEEDS = (
    ("client.active@example.test", Role.CLIENT, "Active Client", "Active", 2, ["Low Sodium"]),
    ("client.inactive@example.test", Role.CLIENT, "Inactive Client", "Inactive", 1, []),
    ("client.pending@example.test", Role.CLIENT, "Pending Client", "Pending", 4, ["Vegetarian"]),
    ("volunteer@example.test", Role.VOLUNTEER, "Demo Volunteer", None, None, None),
    (
        "warehouse.staff@example.test",
        Role.WAREHOUSE_STAFF,
        "Demo Warehouse Staff",
        None,
        None,
        None,
    ),
    (
        "warehouse.manager@example.test",
        Role.WAREHOUSE_MANAGER,
        "Demo Warehouse Manager",
        None,
        None,
        None,
    ),
    ("director@example.test", Role.DIRECTOR, "Demo Director", None, None, None),
)

PRODUCT_SEEDS = (
    {
        "sku": "SYN-OATS-001",
        "barcode": "000000000001",
        "name": "Synthetic Rolled Oats",
        "category": "Grains",
        "sugar_g": 1,
        "sodium_mg": 0,
        "sat_fat_g": 0.5,
        "potassium_mg": 120,
        "ingredients_text": "Synthetic oats",
        "allergens": [],
        "diet_flags": ["is_vegan"],
        "weight_lb": 1.5,
    },
    {
        "sku": "SYN-BEANS-001",
        "barcode": "000000000002",
        "name": "Synthetic Black Beans",
        "category": "Canned Goods",
        "sugar_g": 1,
        "sodium_mg": 420,
        "sat_fat_g": 0,
        "potassium_mg": 360,
        "ingredients_text": "Synthetic beans",
        "allergens": [],
        "diet_flags": ["is_vegan", "contains_gluten"],
        "weight_lb": 1.0,
    },
    {
        "sku": "SYN-SOUP-001",
        "barcode": "000000000003",
        "name": "Synthetic Vegetable Soup",
        "category": "Canned Goods",
        "sugar_g": 8,
        "sodium_mg": 1100,
        "sat_fat_g": 1,
        "potassium_mg": 260,
        "ingredients_text": "Synthetic vegetables, synthetic broth",
        "allergens": ["contains_dairy"],
        "diet_flags": ["contains_dairy"],
        "weight_lb": 1.2,
    },
    {
        "sku": "SYN-CRACK-001",
        "barcode": "000000000004",
        "name": "Synthetic Nut Crackers",
        "category": "Grains",
        "sugar_g": 6,
        "sodium_mg": 180,
        "sat_fat_g": 2,
        "potassium_mg": 90,
        "ingredients_text": "Synthetic wheat, synthetic tree nuts",
        "allergens": ["contains_tree_nut"],
        "diet_flags": ["contains_gluten", "contains_tree_nut"],
        "weight_lb": 0.8,
    },
)

DONOR_SEEDS = (
    ("Synthetic Community Pantry", "DONOR-SYN-001"),
    ("Synthetic Neighborhood Fund", "DONOR-SYN-002"),
)

GRANT_SEEDS = (
    ("Synthetic Nourishment Grant", "GRANT-SYN-001"),
    ("Synthetic Access Grant", "GRANT-SYN-002"),
)


def seed_users(database: Session) -> dict[str, User]:
    seeded: dict[str, User] = {}
    for email, role, name, enrollment, household_size, restrictions in USER_SEEDS:
        user = database.scalar(select(User).where(User.email_hash == email_lookup_hash(email)))
        if user is None:
            user = User(
                email=email,
                email_hash=email_lookup_hash(email),
                password_hash=hash_password(SYNTHETIC_PASSWORD),
                role=role.value,
                is_active=True,
            )
            database.add(user)
            database.flush()
        seeded[email] = user

        if role is Role.CLIENT:
            client = database.get(Client, user.id)
            if client is None:
                client = Client(
                    user_id=user.id,
                    name=name,
                    Household_Size=household_size,
                    Client_Enrollment_Status=enrollment,
                    Dietary_Tier_ID=dietary_tier_id(restrictions or []),
                )
                database.add(client)
                database.flush()
            if database.get(DietaryProfile, client.user_id) is None:
                database.add(
                    DietaryProfile(
                        client_id=client.user_id,
                        restrictions=json.dumps(restrictions or []),
                        allergies="[]",
                        preferences="[]",
                    )
                )
    database.commit()
    return seeded


def seed_catalog(database: Session) -> None:
    donors = []
    for name, attribution_label in DONOR_SEEDS:
        donor = database.scalar(select(Donor).where(Donor.attribution_label == attribution_label))
        if donor is None:
            donor = Donor(name=name, attribution_label=attribution_label)
            database.add(donor)
        donors.append(donor)

    grants = []
    for name, attribution_label in GRANT_SEEDS:
        grant = database.scalar(select(Grant).where(Grant.attribution_label == attribution_label))
        if grant is None:
            grant = Grant(name=name, attribution_label=attribution_label)
            database.add(grant)
        grants.append(grant)
    database.flush()

    today = date.today()
    for index, values in enumerate(PRODUCT_SEEDS):
        product = database.scalar(select(Product).where(Product.sku == values["sku"]))
        if product is None:
            product = Product(**values, source="seed")
            database.add(product)
            database.flush()
        if not database.scalar(select(InventoryLot).where(InventoryLot.product_id == product.id)):
            database.add_all(
                [
                    InventoryLot(
                        product_id=product.id,
                        quantity=12 + index,
                        received_at=datetime.now(UTC) - timedelta(days=index + 1),
                        expiration_date=today + timedelta(days=5 + index * 10),
                        aisle=f"A{index + 1}",
                        shelf=f"S{index + 1}",
                        bin=f"B{index + 1}",
                        reorder_threshold=4,
                        donor_id=donors[index % len(donors)].id,
                        grant_id=grants[index % len(grants)].id,
                    ),
                    InventoryLot(
                        product_id=product.id,
                        quantity=6,
                        received_at=datetime.now(UTC),
                        expiration_date=today + timedelta(days=45 + index * 10),
                        aisle=f"A{index + 1}",
                        shelf=f"S{index + 1}",
                        bin=f"B{index + 5}",
                        reorder_threshold=4,
                        donor_id=donors[index % len(donors)].id,
                        grant_id=grants[index % len(grants)].id,
                    ),
                ]
            )
    database.commit()


def main() -> None:
    from app.db import SessionLocal

    database = SessionLocal()
    try:
        seed_users(database)
        seed_catalog(database)
    finally:
        database.close()


if __name__ == "__main__":
    main()
