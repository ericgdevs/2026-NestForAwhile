from cryptography.fernet import Fernet
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db import Base
from app.models import Client, DietaryProfile, User
from seed.load import SYNTHETIC_PASSWORD, seed_users


def test_seed_users_creates_synthetic_roles_clients_and_profiles(monkeypatch):
    monkeypatch.setenv("FIELD_ENCRYPTION_KEY", Fernet.generate_key().decode())
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as database:
        seeded = seed_users(database)
        users = database.scalars(select(User)).all()
        clients = database.scalars(select(Client)).all()
        profiles = database.scalars(select(DietaryProfile)).all()

    assert len(seeded) == 7
    assert len(users) == 7
    assert {user.role for user in users} == {
        "Client",
        "Volunteer",
        "Warehouse Staff",
        "Warehouse Manager",
        "Director",
    }
    assert len(clients) == 3
    assert len(profiles) == 3
    assert SYNTHETIC_PASSWORD == "demo-password"
