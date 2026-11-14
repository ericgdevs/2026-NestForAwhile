from alembic import command
from alembic.config import Config
from sqlalchemy import inspect
from sqlmodel import SQLModel

from app import models  # noqa: F401
from app.db import make_engine


def test_upgrade_head_creates_all_tables(tmp_path, monkeypatch):
    url = f"sqlite:///{tmp_path / 'mig.db'}"
    monkeypatch.setenv("DATABASE_URL", url)
    command.upgrade(Config("alembic.ini"), "head")
    created = set(inspect(make_engine(url)).get_table_names())
    assert set(SQLModel.metadata.tables) <= created


def test_lots_have_donor_and_grant_columns_after_upgrade(tmp_path, monkeypatch):
    url = f"sqlite:///{tmp_path / 'mig.db'}"
    monkeypatch.setenv("DATABASE_URL", url)
    command.upgrade(Config("alembic.ini"), "head")
    columns = {c["name"] for c in inspect(make_engine(url)).get_columns("inventory_lots")}
    assert {"donor_id", "grant_id"} <= columns
