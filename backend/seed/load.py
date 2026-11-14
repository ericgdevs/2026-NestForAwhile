from __future__ import annotations

import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import Role, email_lookup_hash, hash_password
from app.models import Client, DietaryProfile, User
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


def main() -> None:
    from app.db import SessionLocal

    database = SessionLocal()
    try:
        seed_users(database)
    finally:
        database.close()


if __name__ == "__main__":
    main()
