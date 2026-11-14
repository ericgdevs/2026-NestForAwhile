from sqlalchemy import text
from sqlmodel import select

from app.db import make_engine
from app.models import DietaryProfile, EnrollmentStatus, Role, User, ClientProfile
from app.auth import hash_password


def test_engine_uses_database_url(tmp_path):
    engine = make_engine(f"sqlite:///{tmp_path / 'x.db'}")
    with engine.connect() as c:
        assert c.execute(text("select 1")).scalar() == 1


def test_encrypted_fields_not_plaintext_at_rest(session):
    session.add(User(email="a@example.test", email_hash="h", password_hash=hash_password("pw"), role=Role.CLIENT))
    session.commit()
    session.add(ClientProfile(user_id=1, name="Test Client", Household_Size=3,
                              Client_Enrollment_Status=EnrollmentStatus.ACTIVE))
    session.add(DietaryProfile(client_id=1, allergies='["Nut Allergy"]'))
    session.commit()
    raw = session.connection().execute(text("select allergies from dietary_profiles")).scalar()
    assert "Nut Allergy" not in raw
    assert session.exec(select(DietaryProfile)).one().allergies == '["Nut Allergy"]'
    assert "a@example.test" not in session.connection().execute(text("select email from users")).scalar()


def test_official_field_names_exist():
    from app import models
    assert {"Client_Enrollment_Status", "Household_Size", "Dietary_Tier_ID"} <= set(models.ClientProfile.model_fields)
    assert "Shopping_Session_Token" in models.ShoppingSession.model_fields
    assert "Max_Floor_Capacity" in models.CapacitySettings.model_fields
