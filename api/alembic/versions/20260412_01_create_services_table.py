"""create services table

Revision ID: 20260412_01
Revises:
Create Date: 2026-04-12 14:40:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260412_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "services",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("url", sa.String(length=2048), nullable=False),
        sa.Column("expected_status", sa.Integer(), nullable=False),
        sa.Column("timeout_seconds", sa.Integer(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("services")
