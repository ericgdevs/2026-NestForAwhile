from pathlib import Path

from sqlalchemy import create_engine, inspect

from alembic import command
from alembic.config import Config


def test_upgrade_head_creates_all_tables(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'migration.db'}"
    config = Config(str(Path(__file__).parents[1] / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", database_url)

    command.upgrade(config, "head")

    tables = set(inspect(create_engine(database_url)).get_table_names())
    assert {
        "users",
        "clients",
        "dietary_profiles",
        "visits",
        "products",
        "inventory_lots",
        "inventory_movements",
        "audit_events",
        "shopping_sessions",
        "capacity_settings",
        "queue_entries",
        "carts",
        "cart_items",
        "recommendations",
        "checkouts",
        "checkout_items",
        "interventions",
        "donors",
        "grants",
        "reports",
        "ai_requests",
    }.issubset(tables)
