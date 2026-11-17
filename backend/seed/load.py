from __future__ import annotations

import csv
import json
import random
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import Role, email_lookup_hash, hash_password
from app.models import (
    Cart,
    CartItem,
    Checkout,
    CheckoutItem,
    Client,
    ClientMedicalProfile,
    DietaryProfile,
    Donor,
    Grant,
    HouseholdMember,
    InventoryLot,
    InventoryMovement,
    Product,
    ShoppingSession,
    User,
    Visit,
)
from app.rules.tiers import dietary_tier_id
from app.services.household import effective_choices

SYNTHETIC_PASSWORD = "demo-password"

USER_SEEDS = (
    ("client.active@example.test", Role.CLIENT, "Active Client", "Active", 2, ["Low Sodium"]),
    ("client.inactive@example.test", Role.CLIENT, "Inactive Client", "Inactive", 1, []),
    ("client.pending@example.test", Role.CLIENT, "Pending Client", "Pending", 6, ["Vegetarian"]),
    ("client.diabetes.htn@example.test", Role.CLIENT, "Diabetes HTN Client", "Active", 1, []),
    ("client.ckd.htn@example.test", Role.CLIENT, "CKD HTN Client", "Active", 2, []),
    ("client.diabetes.ckd@example.test", Role.CLIENT, "Diabetes CKD Client", "Active", 1, []),
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

# Synthetic households: (nickname, age, restrictions, allergies, ICD-10 codes). Household size,
# tier and profile are derived from these. client.inactive gets one "Person 1" by default.
# Personas: active = child nut allergy; pending = large household; the other three overlap
# diabetes (E11), hypertension (I10) and CKD (N18), where the strictest rule wins.
MEMBER_SEEDS = {
    "client.active@example.test": (
        ("Person 1", 38, ["Low Sodium"], [], []),
        ("Little one", 7, [], ["Nut Allergy"], []),
    ),
    "client.pending@example.test": (
        ("Person 1", 41, ["Vegetarian"], [], []),
        ("Person 2", 39, [], [], []),
        ("Teen", 15, [], [], []),
        ("Child 1", 10, [], ["Dairy Free"], []),
        ("Child 2", 6, [], [], []),
        ("Grandparent", 68, [], [], ["I10"]),
    ),
    "client.diabetes.htn@example.test": (("Person 1", 62, [], [], ["E11", "I10"]),),
    "client.ckd.htn@example.test": (
        ("Person 1", 58, [], [], ["N18", "I10"]),
        ("Person 2", 55, [], [], []),
    ),
    "client.diabetes.ckd@example.test": (("Person 1", 66, [], [], ["E11", "N18"]),),
}

# To add a real demo product, append a dict here with a real UPC-A/EAN-13 in "barcode"
# (the SKU stays our own label code). Scans and /labels pick it up on the next seed run.
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


def _ensure_members(client: Client, members) -> None:
    """Add any seeded member missing by nickname (and its ICD-10 codes); never touch the rest."""
    have = {member.nickname: member for member in client.members}
    for nickname, age, restrictions, allergies, codes in members:
        member = have.get(nickname)
        if member is None:
            member = HouseholdMember(
                position=max((m.position for m in client.members), default=0) + 1,
                nickname=nickname,
                age=age,
                restrictions=json.dumps(restrictions),
                allergies=json.dumps(allergies),
            )
            client.members.append(member)
        if codes and member.medical_profile is None:
            member.medical_profile = ClientMedicalProfile(icd10_codes=json.dumps(codes))


def _sync_household(client: Client, profile: DietaryProfile) -> None:
    """Keep size, tier and profile in step with the members, as the sign-up route does."""
    effective = [effective_choices(member) for member in client.members]
    restrictions = {r for choices in effective for r in choices["restrictions"]}
    allergies = {a for choices in effective for a in choices["allergies"]}
    client.Household_Size = len(client.members)
    client.Dietary_Tier_ID = dietary_tier_id(restrictions | allergies)  # strictest member wins
    profile.restrictions = json.dumps(sorted(restrictions))
    profile.allergies = json.dumps(sorted(allergies))


def _upsert_user(database: Session, email, role, name, enrollment, household_size, restrictions):
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
        profile = database.get(DietaryProfile, client.user_id)
        if profile is None:
            profile = DietaryProfile(
                client_id=client.user_id,
                restrictions=json.dumps(restrictions or []),
                allergies="[]",
                preferences="[]",
            )
            database.add(profile)
        members = MEMBER_SEEDS.get(email, (("Person 1", None, restrictions or [], [], []),))
        _ensure_members(client, members)
        _sync_household(client, profile)
    return user


def seed_users(database: Session) -> dict[str, User]:
    seeded = {entry[0]: _upsert_user(database, *entry) for entry in USER_SEEDS}
    database.commit()
    return seeded


SHELF_LIFE_DAYS = {
    "Produce": 8,
    "Proteins": 12,
    "Dairy": 21,
    "Grains": 270,
    "Canned Goods": 540,
    "Pantry": 365,
    "Snacks": 120,
    "Beverages": 180,
}
CATALOG_PATH = Path(__file__).with_name("catalog.csv")
NUMBER_FIELDS = (
    "serving_size_g", "calories", "sodium_mg", "sugar_g", "added_sugar_g", "sat_fat_g",
    "fiber_g", "protein_g", "potassium_mg", "phosphorus_mg", "carbs_g", "weight_lb",
)  # fmt: skip


def load_catalog_rows() -> list[dict]:
    """catalog.csv as {"product": Product fields, "aisle", "shelf", "bin", "quantity"}."""
    with CATALOG_PATH.open(encoding="utf-8", newline="") as catalog_file:
        rows = list(csv.DictReader(catalog_file))
    return [
        {
            "product": {
                **{
                    key: row[key]
                    for key in ("sku", "barcode", "name", "category", "ingredients_text")
                },
                **{key: float(row[key]) for key in NUMBER_FIELDS},
                "allergens": [tag for tag in row["allergens"].split(";") if tag],
                "diet_flags": [tag for tag in row["diet_flags"].split(";") if tag],
            },
            "aisle": row["aisle"],
            "shelf": row["shelf"],
            "bin": row["bin"],
            "quantity": int(row["quantity"]),
        }
        for row in rows
    ]


def _upsert_product(database: Session, values: dict) -> Product:
    """Find by SKU; create if missing, otherwise only fill fields that are still empty."""
    product = database.scalar(select(Product).where(Product.sku == values["sku"]))
    if product is None:
        product = Product(**values, source="seed")
        database.add(product)
    else:
        for field, value in values.items():
            if getattr(product, field) is None:
                setattr(product, field, value)
    database.flush()
    return product


def _add_lots_once(database: Session, product: Product, donor, grant, lots) -> None:
    """lots: (quantity, days since received, days to expiry, aisle, shelf, bin)."""
    if database.scalar(select(InventoryLot).where(InventoryLot.product_id == product.id)):
        return
    for quantity, received_days_ago, expires_in_days, aisle, shelf, bin_ in lots:
        database.add(
            InventoryLot(
                product_id=product.id,
                quantity=quantity,
                received_at=datetime.now(UTC) - timedelta(days=received_days_ago),
                expiration_date=date.today() + timedelta(days=expires_in_days),
                aisle=aisle,
                shelf=shelf,
                bin=bin_,
                reorder_threshold=4,
                donor_id=donor.id,
                grant_id=grant.id,
            )
        )


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

    for index, values in enumerate(PRODUCT_SEEDS):
        product = _upsert_product(database, values)
        _add_lots_once(
            database,
            product,
            donors[index % len(donors)],
            grants[index % len(grants)],
            [
                (
                    12 + index,
                    index + 1,
                    5 + index * 10,
                    f"A{index + 1}",
                    f"S{index + 1}",
                    f"B{index + 1}",
                ),
                (6, 0, 45 + index * 10, f"A{index + 1}", f"S{index + 1}", f"B{index + 5}"),
            ],
        )
    for index, row in enumerate(load_catalog_rows()):
        product = _upsert_product(database, row["product"])
        shelf_life = SHELF_LIFE_DAYS[row["product"]["category"]]
        place = (row["aisle"], row["shelf"])
        _add_lots_once(
            database,
            product,
            donors[index % len(donors)],
            grants[index % len(grants)],
            [
                (row["quantity"], 3, shelf_life // 2, *place, row["bin"]),
                (row["quantity"] // 2, 0, shelf_life, *place, f"{row['bin']}-2"),
            ],
        )
    database.commit()


DEMO_RESTRICTIONS = ([], ["Low Sodium"], ["Low Sugar"], ["Heart Healthy"], ["Vegetarian"], ["Kidney Friendly"])


def _demo_visit(database, rng, client_id, volunteer_id, products, days_ago, token):
    """One completed past visit: session, cart, checkout, stock taken from the oldest lot."""
    ended = datetime.now(UTC) - timedelta(days=days_ago, hours=rng.randint(0, 5))
    session = ShoppingSession(
        Shopping_Session_Token=token,
        client_id=client_id,
        status="completed",
        started_at=ended - timedelta(minutes=rng.randint(20, 50)),
        ended_at=ended,
    )
    database.add(session)
    database.flush()
    cart = Cart(session_id=session.id)
    checkout = Checkout(
        session_id=session.id, validated_by=volunteer_id, status="completed", completed_at=ended
    )
    database.add_all([cart, checkout])
    database.flush()
    pounds = 0.0
    for product in rng.sample(products, rng.randint(3, 6)):
        quantity = rng.randint(1, 3)
        lot = database.scalar(
            select(InventoryLot)
            .where(InventoryLot.product_id == product.id, InventoryLot.quantity >= quantity + 6)
            .order_by(InventoryLot.expiration_date, InventoryLot.id)
        )
        if lot is None:
            continue
        lot.quantity -= quantity
        pounds += (product.weight_lb or 0) * quantity
        database.add_all(
            [
                CartItem(
                    cart_id=cart.id,
                    product_id=product.id,
                    quantity=quantity,
                    added_at=ended,
                    from_recommendation=rng.random() < 0.6,
                ),
                CheckoutItem(
                    checkout_id=checkout.id,
                    product_id=product.id,
                    lot_id=lot.id,
                    quantity=quantity,
                    status_at_checkout="Approved",
                ),
                InventoryMovement(
                    lot_id=lot.id,
                    change=-quantity,
                    reason="checkout",
                    ref_id=checkout.id,
                    created_at=ended,
                ),
            ]
        )
    checkout.total_lb = pounds
    database.add(
        Visit(
            client_id=client_id,
            session_id=session.id,
            started_at=session.started_at,
            completed_at=ended,
            pounds_distributed=pounds,
        )
    )


def seed_demo_history(database: Session) -> None:
    """Synthetic past visits, sign-ups waiting for approval and low shelves, so the manager and
    director screens have something to show. Runs once; the marker is the first demo family."""
    marker = "family.01@example.test"
    if database.scalar(select(User).where(User.email_hash == email_lookup_hash(marker))):
        return
    rng = random.Random(7)  # fixed seed: every demo database looks the same
    volunteer = database.scalar(select(User).where(User.role == Role.VOLUNTEER.value))
    products = database.scalars(select(Product).where(Product.source == "seed")).all()

    for number in range(1, 13):
        restrictions = DEMO_RESTRICTIONS[number % len(DEMO_RESTRICTIONS)]
        family = _upsert_user(
            database, f"family.{number:02d}@example.test", Role.CLIENT,
            f"Demo Family {number:02d}", "Active", 1, restrictions,
        )  # fmt: skip
        for visit in range(rng.randint(1, 4)):
            token = f"demo-history-{number:02d}-{visit}"
            _demo_visit(database, rng, family.id, volunteer.id, products, rng.randint(1, 55), token)
    for number in range(1, 4):
        newcomer = _upsert_user(
            database, f"newcomer.{number:02d}@example.test", Role.CLIENT,
            f"Demo Newcomer {number:02d}", "Pending", 1, [],
        )  # fmt: skip
        database.get(Client, newcomer.id).created_at = datetime.now(UTC) - timedelta(
            hours=number * 7
        )

    for product in rng.sample(products, 8):  # run one lot of each low so Restock has rows
        lot = database.scalar(
            select(InventoryLot).where(InventoryLot.product_id == product.id).order_by(InventoryLot.id)
        )
        left = rng.randint(0, 3)
        database.add(InventoryMovement(lot_id=lot.id, change=left - lot.quantity, reason="audit"))
        lot.quantity = left
    database.commit()


def main() -> None:
    from app.db import SessionLocal

    database = SessionLocal()
    try:
        seed_users(database)
        seed_catalog(database)
        seed_demo_history(database)
    finally:
        database.close()


if __name__ == "__main__":
    main()
