"""link inventory lots to donors and grants

Revision ID: 0002
Revises: 0001
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, Sequence[str], None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Nullable, so existing lots stay valid; batch mode lets SQLite add the foreign keys
    with op.batch_alter_table("inventory_lots") as batch:
        batch.add_column(sa.Column("donor_id", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("grant_id", sa.Integer(), nullable=True))
        batch.create_foreign_key("fk_inventory_lots_donor_id", "donors", ["donor_id"], ["id"])
        batch.create_foreign_key("fk_inventory_lots_grant_id", "grants", ["grant_id"], ["id"])


def downgrade() -> None:
    with op.batch_alter_table("inventory_lots") as batch:
        batch.drop_constraint("fk_inventory_lots_grant_id", type_="foreignkey")
        batch.drop_constraint("fk_inventory_lots_donor_id", type_="foreignkey")
        batch.drop_column("grant_id")
        batch.drop_column("donor_id")
