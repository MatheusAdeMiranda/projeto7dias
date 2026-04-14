"""create check_results table

Revision ID: 20260414_02
Revises: 20260412_01
Create Date: 2026-04-14 00:00:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260414_02"
down_revision = "20260412_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "check_results",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column(
            "service_id",
            sa.Integer(),
            sa.ForeignKey("services.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("response_time_ms", sa.Integer(), nullable=True),
        sa.Column("http_status_code", sa.Integer(), nullable=True),
        sa.Column("checked_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("error_message", sa.String(length=500), nullable=True),
    )
    op.create_index("ix_check_results_service_id", "check_results", ["service_id"])


def downgrade() -> None:
    op.drop_index("ix_check_results_service_id", table_name="check_results")
    op.drop_table("check_results")
