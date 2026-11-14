"""Write a client's household. Medical conditions only pass through here; they are never stored."""

from __future__ import annotations

import json

from pydantic import BaseModel, Field
from sqlalchemy.orm import object_session

from app.models import Client, DietaryProfile, HouseholdMember
from app.rules.classify import conditions_to_choices
from app.rules.tiers import DIETARY_TIER_IDS, dietary_tier_id


class MemberIn(BaseModel):
    nickname: str | None = Field(default=None, max_length=40)
    age: int | None = Field(default=None, ge=0, le=120)
    restrictions: list[str] = Field(default_factory=list)
    allergies: list[str] = Field(default_factory=list)
    conditions: list[str] = Field(default_factory=list)  # turned into restrictions, then dropped


def validate_members(members: list[MemberIn]) -> None:
    """Raise ValueError with a friendly message for unknown choices or conditions."""
    for member in members:
        unknown = set(member.restrictions + member.allergies).difference(DIETARY_TIER_IDS)
        if unknown:
            raise ValueError(f"Unknown dietary choice(s): {', '.join(sorted(unknown))}")
        conditions_to_choices(member.conditions)


def apply_household(client: Client, members: list[MemberIn]) -> None:
    """Replace the household and keep Household_Size, tier, and the legacy profile in step."""
    validate_members(members)
    rows = []
    for position, member in enumerate(members, start=1):
        from_conditions = conditions_to_choices(member.conditions)
        restrictions = sorted(set(member.restrictions) | set(from_conditions))
        rows.append(
            HouseholdMember(
                position=position,
                nickname=(member.nickname or "").strip() or f"Person {position}",
                age=member.age,
                restrictions=json.dumps(restrictions),
                allergies=json.dumps(sorted(set(member.allergies))),
            )
        )
    client.members.clear()
    if (session := object_session(client)) is not None:
        session.flush()  # delete old rows before inserting the same positions again
    client.members.extend(rows)
    every_restriction = {r for row in rows for r in json.loads(row.restrictions)}
    every_allergy = {a for row in rows for a in json.loads(row.allergies)}
    client.Household_Size = len(rows)
    client.Dietary_Tier_ID = dietary_tier_id(every_restriction | every_allergy)  # strictest member
    if client.dietary_profile is None:
        client.dietary_profile = DietaryProfile(preferences="[]")
    client.dietary_profile.restrictions = json.dumps(sorted(every_restriction))
    client.dietary_profile.allergies = json.dumps(sorted(every_allergy))


def household_view(client: Client) -> list[dict[str, object]]:
    return [
        {
            "nickname": member.nickname,
            "age": member.age,
            "restrictions": json.loads(member.restrictions),
            "allergies": json.loads(member.allergies),
        }
        for member in client.members
    ]
