import json

from sqlmodel import select

from app.models import ClientProfile, DietaryProfile, EnrollmentStatus, Role, User
from seed.load import seed_all


def test_seed_creates_one_user_per_role_and_five_personas(session):
    seed_all(session)
    roles = {u.role for u in session.exec(select(User)).all()}
    assert roles == set(Role)
    assert len(session.exec(select(ClientProfile)).all()) == 5


def test_personas_cover_status_household_tier_and_overlap(session):
    seed_all(session)
    clients = session.exec(select(ClientProfile).order_by(ClientProfile.user_id)).all()
    assert any(c.Client_Enrollment_Status != EnrollmentStatus.ACTIVE for c in clients)
    assert len({c.Household_Size for c in clients}) >= 4
    kidney_diabetes = clients[1]
    assert kidney_diabetes.Dietary_Tier_ID == 4  # strictest wins
    restrictions = json.loads(session.get(DietaryProfile, kidney_diabetes.user_id).restrictions)
    assert {"Kidney Friendly", "Low Sugar"} <= set(restrictions)


def test_seed_is_idempotent_and_uses_synthetic_emails(session):
    seed_all(session)
    seed_all(session)
    users = session.exec(select(User)).all()
    assert len(users) == 9
    assert all(u.email.endswith("@example.test") for u in users)
