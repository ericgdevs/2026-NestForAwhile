"""Household members, Client_Medical_Profile, client approval, saved recipes, shopping list."""

import sqlalchemy as sa

from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    # 0001 builds tables from the current models, so fresh databases already have this one.
    if "household_members" not in sa.inspect(bind).get_table_names():
        op.create_table(
            "household_members",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("client_id", sa.Integer(), sa.ForeignKey("clients.user_id"), nullable=False),
            sa.Column("position", sa.Integer(), nullable=False),
            sa.Column("nickname", sa.String(40), nullable=False),
            sa.Column("age", sa.Integer(), nullable=True),
            sa.Column("restrictions", sa.Text(), nullable=False),
            sa.Column("allergies", sa.Text(), nullable=False),
            sa.UniqueConstraint("client_id", "position"),
        )
    if "saved_recipes" not in sa.inspect(bind).get_table_names():
        op.create_table(
            "saved_recipes",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("client_id", sa.Integer(), sa.ForeignKey("clients.user_id"), nullable=False),
            sa.Column("title", sa.String(80), nullable=False),
            sa.Column("recipe", sa.JSON(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
        )
        op.create_index("ix_saved_recipes_client_id", "saved_recipes", ["client_id"])
    if "shopping_list_items" not in sa.inspect(bind).get_table_names():
        op.create_table(
            "shopping_list_items",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("client_id", sa.Integer(), sa.ForeignKey("clients.user_id"), nullable=False),
            sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id"), nullable=True),
            sa.Column("text", sa.String(120), nullable=False),
            sa.Column("source", sa.String(16), nullable=False),
            sa.Column("recipe", sa.JSON(), nullable=True),
            sa.Column("ticked", sa.Boolean(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
        )
        op.create_index("ix_shopping_list_items_client_id", "shopping_list_items", ["client_id"])
    if "client_medical_profiles" not in sa.inspect(bind).get_table_names():
        op.create_table(
            "client_medical_profiles",
            sa.Column(
                "member_id",
                sa.Integer(),
                sa.ForeignKey("household_members.id", ondelete="CASCADE"),
                primary_key=True,
            ),
            sa.Column("icd10_codes", sa.Text(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
        )
    client_columns = {column["name"] for column in sa.inspect(bind).get_columns("clients")}
    if "approved_by" not in client_columns:
        with op.batch_alter_table("clients") as batch:
            batch.add_column(sa.Column("approved_by", sa.Integer(), nullable=True))
            batch.add_column(sa.Column("approved_at", sa.DateTime(), nullable=True))
    # Ciphertext is copied as-is: same key, same EncryptedText column type.
    op.execute(
        """
        INSERT INTO household_members (client_id, position, nickname, age, restrictions, allergies)
        SELECT profile.client_id, 1, 'Person 1', NULL, profile.restrictions, profile.allergies
        FROM dietary_profiles AS profile
        WHERE NOT EXISTS (
            SELECT 1 FROM household_members AS member WHERE member.client_id = profile.client_id
        )
        """
    )


def downgrade() -> None:
    with op.batch_alter_table("clients") as batch:
        batch.drop_column("approved_at")
        batch.drop_column("approved_by")
    op.drop_table("client_medical_profiles")
    op.drop_table("shopping_list_items")
    op.drop_table("saved_recipes")
    op.drop_table("household_members")
