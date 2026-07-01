"""Add survapp_user table for authentication

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-30
"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "survapp_user",
        sa.Column("id",            sa.Integer(),              nullable=False),
        sa.Column("username",      sa.String(100),            nullable=False),
        sa.Column("password_hash", sa.String(255),            nullable=False),
        sa.Column("full_name",     sa.String(200)),
        sa.Column("role",          sa.String(50),             nullable=False,
                  server_default="operator"),
        sa.Column("is_active",     sa.Boolean(),              nullable=False,
                  server_default="true"),
        sa.Column("last_login",    sa.DateTime(timezone=True)),
        sa.Column("created_at",    sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username", name="uq_user_username"),
    )
    op.create_index("ix_user_id",       "survapp_user", ["id"])
    op.create_index("ix_user_username", "survapp_user", ["username"], unique=True)


def downgrade() -> None:
    op.drop_table("survapp_user")
