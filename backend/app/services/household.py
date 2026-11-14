"""Write a client's household. ICD-10 codes go to the encrypted Client_Medical_Profile (Epic 2)."""

from __future__ import annotations

import json

from pydantic import BaseModel, Field
from sqlalchemy.orm import object_session

from app.models import Client, ClientMedicalProfile, DietaryProfile, HouseholdMember
from app.rules.classify import conditions_to_choices
from app.rules.tiers import DIETARY_TIER_IDS, dietary_tier_id


class MemberIn(BaseModel):
    nickname: str | None = Field(default=None, max_length=40)
    age: int | None = Field(default=None, ge=0, le=120)
    restrictions: list[str] = Field(default_factory=list)
    allergies: list[str] = Field(default_factory=list)
    conditions: list[str] = Field(default_factory=list, max_length=20)  # ICD-10 codes


def validate_members(members: list[MemberIn]) -> None:
    """Raise ValueError with a friendly message for unknown choices or ICD-10 codes."""
    for member in members:
        unknown = set(member.restrictions + member.allergies).difference(DIETARY_TIER_IDS)
        if unknown:
            raise ValueError(f"Unknown dietary choice(s): {', '.join(sorted(unknown))}")
        conditions_to_choices(member.conditions)


def member_codes(member: HouseholdMember) -> list[str]:
    return json.loads(member.medical_profile.icd10_codes) if member.medical_profile else []


def effective_choices(member: HouseholdMember) -> dict[str, list[str]]:
    """What the rules engine uses: picked restrictions plus those mapped from ICD-10 codes."""
    picked = json.loads(member.restrictions)
    return {
        "restrictions": sorted(set(picked) | set(conditions_to_choices(member_codes(member)))),
        "allergies": json.loads(member.allergies),
    }


def apply_household(client: Client, members: list[MemberIn]) -> None:
    """Replace the household and keep Household_Size, tier, and the legacy profile in step."""
    validate_members(members)
    rows = []
    for position, member in enumerate(members, start=1):
        row = HouseholdMember(
            position=position,
            nickname=(member.nickname or "").strip() or f"Person {position}",
            age=member.age,
            restrictions=json.dumps(sorted(set(member.restrictions))),
            allergies=json.dumps(sorted(set(member.allergies))),
        )
        if member.conditions:
            row.medical_profile = ClientMedicalProfile(
                icd10_codes=json.dumps(sorted(set(member.conditions)))
            )
        rows.append(row)
    client.members.clear()
    if (session := object_session(client)) is not None:
        session.flush()  # delete old rows before inserting the same positions again
    client.members.extend(rows)
    effective = [effective_choices(row) for row in rows]
    every_restriction = {r for e in effective for r in e["restrictions"]}
    every_allergy = {a for e in effective for a in e["allergies"]}
    client.Household_Size = len(rows)
    client.Dietary_Tier_ID = dietary_tier_id(every_restriction | every_allergy)  # strictest member
    if client.dietary_profile is None:
        client.dietary_profile = DietaryProfile(preferences="[]")
    client.dietary_profile.restrictions = json.dumps(sorted(every_restriction))
    client.dietary_profile.allergies = json.dumps(sorted(every_allergy))


def household_view(client: Client) -> list[dict[str, object]]:
    """The client's own view of their household, including their ICD-10 codes."""
    return [
        {
            "nickname": member.nickname,
            "age": member.age,
            "restrictions": json.loads(member.restrictions),
            "allergies": json.loads(member.allergies),
            "conditions": member_codes(member),
        }
        for member in client.members
    ]
