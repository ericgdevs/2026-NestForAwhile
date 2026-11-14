import json

from sqlmodel import Session

from app.models import ClientProfile, DietaryProfile
from app.rules.tiers import tier_for


def assign_tier(session: Session, client: ClientProfile) -> int:
    """Recompute Dietary_Tier_ID from the stored profile (strictest wins); caller commits."""
    stored = session.get(DietaryProfile, client.user_id)
    selected = [r for field in (stored and (stored.restrictions, stored.allergies)) or () if field for r in json.loads(field)]
    client.Dietary_Tier_ID = tier_for(selected)
    session.add(client)
    return client.Dietary_Tier_ID
