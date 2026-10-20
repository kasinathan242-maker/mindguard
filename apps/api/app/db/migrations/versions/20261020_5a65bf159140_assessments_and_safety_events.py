"""assessments and safety events

Revision ID: 5a65bf159140
Revises: a45bf76cdeae
Create Date: 2026-10-20 20:19:41.419701
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "5a65bf159140"
down_revision: str | None = "a45bf76cdeae"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "assessments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("type", sa.String(length=8), nullable=False),
        sa.Column(
            "answers",
            sa.JSON().with_variant(postgresql.ARRAY(sa.SmallInteger()), "postgresql"),
            nullable=False,
        ),
        sa.Column("total", sa.Integer(), nullable=False),
        sa.Column("severity_band", sa.String(length=24), nullable=False),
        sa.Column("safety_item_positive", sa.Boolean(), nullable=False),
        sa.Column("functional_difficulty", sa.SmallInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_assessments_user_id_users"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_assessments")),
    )
    op.create_index(op.f("ix_assessments_created_at"), "assessments", ["created_at"], unique=False)
    op.create_index(op.f("ix_assessments_user_id"), "assessments", ["user_id"], unique=False)
    op.create_table(
        "safety_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("source", sa.String(length=16), nullable=False),
        sa.Column("level", sa.String(length=16), nullable=False),
        sa.Column("detector", sa.String(length=16), nullable=False),
        sa.Column(
            "resources_shown",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_safety_events_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_safety_events")),
    )
    op.create_index(op.f("ix_safety_events_user_id"), "safety_events", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_safety_events_user_id"), table_name="safety_events")
    op.drop_table("safety_events")
    op.drop_index(op.f("ix_assessments_user_id"), table_name="assessments")
    op.drop_index(op.f("ix_assessments_created_at"), table_name="assessments")
    op.drop_table("assessments")
