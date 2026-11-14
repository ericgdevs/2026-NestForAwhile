import json
from pathlib import Path

from cryptography.fernet import Fernet
from sqlalchemy import create_engine, text

from alembic import command
from alembic.config import Config
from app.models import Client, HouseholdMember, User


def test_seed_gives_active_client_a_two_person_household(database):
    user = database.query(User).filter(User.role == "Client").first()
    client = database.get(Client, user.id)
    members = client.members

    assert [member.nickname for member in members] == ["Person 1", "Little one"]
    assert json.loads(members[1].allergies) == ["Nut Allergy"]
    assert client.Household_Size == len(members)


def test_member_choices_are_encrypted_at_rest(database):
    member = database.query(HouseholdMember).filter_by(nickname="Little one").one()
    stored = database.execute(
        text("SELECT allergies FROM household_members WHERE id = :id"), {"id": member.id}
    ).scalar_one()

    assert "Nut Allergy" not in stored


def test_migration_moves_existing_profiles_into_person_1(tmp_path, monkeypatch):
    monkeypatch.setenv("FIELD_ENCRYPTION_KEY", Fernet.generate_key().decode())
    url = f"sqlite:///{tmp_path / 'm.db'}"
    config = Config(str(Path(__file__).parents[2] / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", url)
    command.upgrade(config, "0002")
    engine = create_engine(url)
    with engine.begin() as connection:
        connection.execute(text("DROP TABLE household_members"))  # simulate a pre-0003 database
        connection.execute(
            text(
                "INSERT INTO users (id, email, email_hash, password_hash, role, is_active,"
                " created_at) VALUES (1, 'x', 'h', 'p', 'Client', 1, '2026-11-14')"
            )
        )
        connection.execute(
            text(
                "INSERT INTO clients (user_id, name, Household_Size, Client_Enrollment_Status,"
                " Dietary_Tier_ID, created_at) VALUES (1, 'x', 1, 'Active', 1, '2026-11-14')"
            )
        )
        connection.execute(
            text(
                "INSERT INTO dietary_profiles (client_id, restrictions, allergies, preferences,"
                " updated_at) VALUES (1, 'cipher-r', 'cipher-a', 'cipher-p', '2026-11-14')"
            )
        )

    command.upgrade(config, "0003")

    with engine.connect() as connection:
        row = connection.execute(
            text("SELECT position, nickname, restrictions, allergies FROM household_members")
        ).one()
    assert tuple(row) == (1, "Person 1", "cipher-r", "cipher-a")
