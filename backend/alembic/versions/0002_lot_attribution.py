"""Link inventory lots to donors and grants."""

import sqlalchemy as sa

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns("inventory_lots")}
    if "donor_id" not in columns:
        op.add_column("inventory_lots", sa.Column("donor_id", sa.Integer(), nullable=True))
    if "grant_id" not in columns:
        op.add_column("inventory_lots", sa.Column("grant_id", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_constraint("fk_inventory_lots_grant_id", "inventory_lots", type_="foreignkey")
    op.drop_constraint("fk_inventory_lots_donor_id", "inventory_lots", type_="foreignkey")
    op.drop_column("inventory_lots", "grant_id")
    op.drop_column("inventory_lots", "donor_id")
