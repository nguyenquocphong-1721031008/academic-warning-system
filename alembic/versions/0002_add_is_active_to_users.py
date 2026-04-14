"""add is_active column to users

Revision ID: 0002_add_is_active_to_users
Revises: 0001_schema_sql_baseline
Create Date: 2026-04-14
"""

from alembic import op
import sqlalchemy as sa


revision = "0002_add_is_active_to_users"
down_revision = "0001_schema_sql_baseline"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.alter_column("users", "is_active", server_default=None)


def downgrade() -> None:
    op.drop_column("users", "is_active")
