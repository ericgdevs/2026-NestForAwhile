"""Idempotent synthetic seed loader. Run from backend/: python -m seed.load"""
import json
import os
from datetime import date, timedelta

from sqlmodel import Session, select

from app.auth import email_digest, hash_password
from app.models import (ClientProfile, DietaryProfile, DietaryTier, DonationSource, GrantFundingStream,
                        InventoryLocation, InventoryLot, Product, Role, User)
from app.rules.matrix import restrictions_for_conditions
from app.rules.tiers import TIERS, tier_for
from seed.catalog import DONORS, GRANTS, PRODUCTS
from seed.personas import PERSONAS, STAFF_USERS

# Synthetic demo password only; override with SEED_PASSWORD
SEED_PASSWORD = os.getenv("SEED_PASSWORD", "demo-password-synthetic")


def load_tiers(session: Session) -> None:
    for tier_id, (name, description) in TIERS.items():
        session.merge(DietaryTier(Dietary_Tier_ID=tier_id, name=name, description=description))
    session.commit()


def _get_or_create_user(session: Session, email: str, role: Role) -> tuple[User, bool]:
    user = session.exec(select(User).where(User.email_hash == email_digest(email))).first()
    if user:
        return user, False
    user = User(email=email, email_hash=email_digest(email), password_hash=hash_password(SEED_PASSWORD), role=role)
    session.add(user)
    session.flush()
    return user, True


def load_users_and_personas(session: Session) -> None:
    for role, email in STAFF_USERS.items():
        _get_or_create_user(session, email, role)
    for persona in PERSONAS:
        user, created = _get_or_create_user(session, persona["email"], Role.CLIENT)
        if not created:
            continue
        restrictions = list(dict.fromkeys(restrictions_for_conditions(persona["conditions"]) + persona["extra_restrictions"]))
        tier = tier_for(restrictions + persona["allergies"])
        session.add(ClientProfile(user_id=user.id, name=persona["name"], Household_Size=persona["household_size"],
                                  Client_Enrollment_Status=persona["status"], Dietary_Tier_ID=tier))
        session.add(DietaryProfile(client_id=user.id, restrictions=json.dumps(restrictions),
                                   allergies=json.dumps(persona["allergies"]), preferences=json.dumps([])))
    session.commit()


def _get_or_create_location(session: Session, aisle: str, shelf: str, bin_: str) -> InventoryLocation:
    location = session.exec(select(InventoryLocation).where(
        InventoryLocation.aisle == aisle, InventoryLocation.shelf == shelf, InventoryLocation.bin == bin_)).first()
    if location is None:
        location = InventoryLocation(aisle=aisle, shelf=shelf, bin=bin_)
        session.add(location)
        session.flush()
    return location


def load_catalog(session: Session) -> None:
    for model, rows in ((DonationSource, DONORS), (GrantFundingStream, GRANTS)):
        for row in rows:
            if not session.exec(select(model).where(model.name == row["name"])).first():
                session.add(model(**row))
    session.flush()
    donor = session.exec(select(DonationSource).order_by(DonationSource.id)).first()
    grant = session.exec(select(GrantFundingStream).order_by(GrantFundingStream.id)).first()
    for index, entry in enumerate(PRODUCTS):
        if session.exec(select(Product).where(Product.barcode == entry["barcode"])).first():
            continue
        fields = {k: v for k, v in entry.items() if k not in ("location", "quantity", "expires_in_days", "reorder_threshold")}
        product = Product(**fields)
        session.add(product)
        session.flush()
        location = _get_or_create_location(session, *entry["location"])
        # Every lot has a donor; alternate lots are also grant-funded so both reports have data
        session.add(InventoryLot(product_id=product.id, location_id=location.id, quantity=entry["quantity"],
                                 expiration_date=date.today() + timedelta(days=entry["expires_in_days"]),
                                 reorder_threshold=entry["reorder_threshold"], donor_id=donor.id,
                                 grant_id=grant.id if index % 2 == 0 else None))
    session.commit()


def seed_all(session: Session) -> None:
    load_tiers(session)
    load_users_and_personas(session)
    load_catalog(session)


if __name__ == "__main__":
    from app.db import engine

    with Session(engine) as s:
        seed_all(s)
