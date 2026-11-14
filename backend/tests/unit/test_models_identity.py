from app.models import Client, DietaryProfile, User, Visit


def test_identity_models_keep_official_columns_and_relationship_tables():
    assert User.__tablename__ == "users"
    assert Client.__table__.c.Household_Size.type.python_type is int
    assert Client.__table__.c.Client_Enrollment_Status.type.python_type is str
    assert DietaryProfile.__table__.c.restrictions is not None
    assert Visit.__table__.c.pounds_distributed is not None
