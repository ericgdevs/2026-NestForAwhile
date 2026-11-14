import json

from sqlmodel import Session

from app.models import ClientProfile, DietaryProfile, EnrollmentStatus, utcnow
from app.schemas import DietaryProfileRead, DietaryProfileWrite
from app.services.tiers import assign_tier


def _loads(value: str | None) -> list[str]:
    return json.loads(value) if value else []


def get_dietary_profile(session: Session, client_id: int) -> DietaryProfileRead:
    client = session.get(ClientProfile, client_id)
    stored = session.get(DietaryProfile, client_id)
    return DietaryProfileRead(
        restrictions=_loads(stored and stored.restrictions),
        allergies=_loads(stored and stored.allergies),
        preferences=_loads(stored and stored.preferences),
        Dietary_Tier_ID=client.Dietary_Tier_ID if client else None,
    )


def rule_restrictions(profile: DietaryProfileRead) -> list[str]:
    """Restrictions plus allergies (e.g. Nut Allergy) are all rows in the rules matrix."""
    return list(dict.fromkeys(profile.restrictions + profile.allergies))


def create_client(session: Session, user_id: int, name: str, household_size: int,
                  status: EnrollmentStatus = EnrollmentStatus.PENDING) -> ClientProfile:
    """Internal only (no public endpoint): new clients start with an empty profile and tier 1."""
    client = ClientProfile(user_id=user_id, name=name, Household_Size=household_size, Client_Enrollment_Status=status)
    session.add(client)
    session.add(DietaryProfile(client_id=user_id, restrictions="[]", allergies="[]", preferences="[]"))
    session.flush()
    assign_tier(session, client)
    session.commit()
    return client


def update_client(session: Session, user_id: int, name: str | None = None, household_size: int | None = None) -> ClientProfile:
    client = _get_client(session, user_id)
    if household_size is not None:
        if household_size < 1:
            raise ValueError("Household_Size must be at least 1")
        client.Household_Size = household_size
    if name is not None:
        client.name = name
    assign_tier(session, client)
    session.commit()
    return client


def save_dietary_profile(session: Session, user_id: int, data: DietaryProfileWrite) -> DietaryProfileRead:
    """Replace the profile and recompute Dietary_Tier_ID in one transaction."""
    client = _get_client(session, user_id)
    stored = session.get(DietaryProfile, user_id) or DietaryProfile(client_id=user_id)
    stored.restrictions = json.dumps(data.restrictions)
    stored.allergies = json.dumps(data.allergies)
    stored.preferences = json.dumps(data.preferences)
    stored.updated_at = utcnow()
    session.add(stored)
    session.flush()
    assign_tier(session, client)
    session.commit()
    return get_dietary_profile(session, user_id)


def _get_client(session: Session, user_id: int) -> ClientProfile:
    client = session.get(ClientProfile, user_id)
    if client is None:
        raise LookupError("Client profile not found")
    return client
