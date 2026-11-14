import json

from sqlmodel import Session

from app.models import ClientProfile, DietaryProfile
from app.schemas import DietaryProfileRead


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
