import json

import pytest
from sqlalchemy import text
from sqlmodel import select

from app.models import ClientProfile, EnrollmentStatus, Role, User
from app.services import profiles


def test_put_profile_saves_and_assigns_tier(login_as, seeded):
    api = login_as(Role.CLIENT)
    body = {"restrictions": ["Vegan", "Kidney Friendly"], "allergies": ["Nut Allergy"], "preferences": ["no cilantro"]}
    resp = api.put("/me/profile", json=body)
    assert resp.status_code == 200
    assert resp.json()["Dietary_Tier_ID"] == 4  # strictest wins
    assert api.get("/me").json()["profile"]["restrictions"] == ["Vegan", "Kidney Friendly"]


def test_tier_recalculates_when_profile_changes(login_as):
    api = login_as(Role.CLIENT)
    assert api.put("/me/profile", json={"restrictions": ["Low Sodium"]}).json()["Dietary_Tier_ID"] == 3
    assert api.put("/me/profile", json={"restrictions": ["Vegan"]}).json()["Dietary_Tier_ID"] == 2
    assert api.put("/me/profile", json={}).json()["Dietary_Tier_ID"] == 1


def test_tier_cannot_be_set_by_client(login_as):
    api = login_as(Role.CLIENT)
    resp = api.put("/me/profile", json={"restrictions": ["Vegan"], "Dietary_Tier_ID": 4})
    assert resp.json()["Dietary_Tier_ID"] == 2


@pytest.mark.parametrize("body", [{"restrictions": ["Keto"]}, {"allergies": ["Shellfish"]}])
def test_unsupported_option_rejected(login_as, body):
    assert login_as(Role.CLIENT).put("/me/profile", json=body).status_code == 422


def test_profile_encrypted_at_rest(login_as, seeded):
    login_as(Role.CLIENT).put("/me/profile", json={"restrictions": ["Low Sugar"], "allergies": ["Nut Allergy"]})
    raw = seeded.connection().execute(text("select restrictions, allergies from dietary_profiles")).all()
    assert all("Low Sugar" not in c and "Nut Allergy" not in c for row in raw for c in row if c)


def test_only_clients_can_save_profile(login_as):
    assert login_as(Role.VOLUNTEER).put("/me/profile", json={}).status_code == 403


def test_create_client_starts_at_tier_one_and_updates_household(session):
    user = User(email="new@example.test", email_hash="x", password_hash="x", role=Role.CLIENT)
    session.add(user)
    session.commit()
    client = profiles.create_client(session, user.id, "Synthetic New", 2)
    assert client.Dietary_Tier_ID == 1 and client.Client_Enrollment_Status == EnrollmentStatus.PENDING
    profiles.save_dietary_profile(session, user.id, profiles.DietaryProfileWrite(restrictions=["Vegan"]))
    profiles.update_client(session, user.id, household_size=5)
    saved = session.get(ClientProfile, user.id)
    assert (saved.Household_Size, saved.Dietary_Tier_ID) == (5, 2)
    with pytest.raises(ValueError):
        profiles.update_client(session, user.id, household_size=0)
