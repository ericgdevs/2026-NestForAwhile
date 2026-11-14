from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth import Role, require_roles
from app.db import get_db
from app.models import Client, DietaryProfile, User
from app.rules.tiers import DIETARY_TIER_IDS, dietary_tier_id

router = APIRouter()


class DietaryProfileRequest(BaseModel):
    restrictions: list[str] = Field(default_factory=list)
    allergies: list[str] = Field(default_factory=list)
    preferences: list[str] = Field(default_factory=list)


@router.put("/me/profile")
def update_profile(
    payload: DietaryProfileRequest,
    current_user: User = Depends(require_roles(Role.CLIENT)),
    database: Session = Depends(get_db),
):
    invalid = set(payload.restrictions).difference(DIETARY_TIER_IDS)
    if invalid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unknown dietary restriction(s): {', '.join(sorted(invalid))}",
        )
    client = database.get(Client, current_user.id)
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client profile not found",
        )
    profile = database.get(DietaryProfile, current_user.id)
    if profile is None:
        profile = DietaryProfile(client_id=current_user.id)
        database.add(profile)
    profile.restrictions = json.dumps(payload.restrictions)
    profile.allergies = json.dumps(payload.allergies)
    profile.preferences = json.dumps(payload.preferences)
    client.Dietary_Tier_ID = dietary_tier_id(payload.restrictions)
    database.commit()
    return {
        **payload.model_dump(),
        "Dietary_Tier_ID": client.Dietary_Tier_ID,
    }
