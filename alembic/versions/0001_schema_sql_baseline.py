"""Baseline schema (schema.sql).

Revision ID: 0001_schema_sql_baseline
Revises:
Create Date: 2026-04-07

"""

from __future__ import annotations

from pathlib import Path

from alembic import op

revision = "0001_schema_sql_baseline"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    root = Path(__file__).resolve().parents[2]
    schema_path = root / "schema.sql"
    sql = schema_path.read_text(encoding="utf-8")
    op.execute(sql)


def downgrade() -> None:
    # DB-first baseline: no automatic down migration.
    pass

