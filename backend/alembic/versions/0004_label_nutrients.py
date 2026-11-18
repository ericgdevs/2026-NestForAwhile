"""Nutrition-label nutrients on products (display only, empty until a lookup fills them)."""

import sqlalchemy as sa

from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None

COLUMNS = ("total_fat_g", "trans_fat_g", "cholesterol_mg", "vitamin_d_mcg", "calcium_mg", "iron_mg")


def upgrade() -> None:
    # 0001 builds tables from the current models, so fresh databases already have these.
    existing = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("products")}
    for name in COLUMNS:
        if name not in existing:
            op.add_column("products", sa.Column(name, sa.Float(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("products") as batch:
        for name in COLUMNS:
            batch.drop_column(name)
