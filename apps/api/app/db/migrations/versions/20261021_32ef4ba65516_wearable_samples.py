"""wearable samples

Revision ID: 32ef4ba65516
Revises: 94f798169545
Create Date: 2026-10-21 00:12:15.748336
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "32ef4ba65516"
down_revision: str | None = "94f798169545"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "wearable_samples",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("metric", sa.String(length=16), nullable=False),
        sa.Column("value", sa.Double(), nullable=False),
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column("source", sa.String(length=16), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_wearable_samples_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_wearable_samples")),
        sa.UniqueConstraint("user_id", "metric", "day", name=op.f("uq_wearable_samples_user_id")),
    )
    op.create_index(
        op.f("ix_wearable_samples_user_id"), "wearable_samples", ["user_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_wearable_samples_user_id"), table_name="wearable_samples")
    op.drop_table("wearable_samples")
