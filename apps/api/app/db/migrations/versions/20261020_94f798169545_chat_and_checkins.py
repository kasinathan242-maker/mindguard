"""chat and checkins

Revision ID: 94f798169545
Revises: 5a65bf159140
Create Date: 2026-10-20 22:01:16.850814
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "94f798169545"
down_revision: str | None = "5a65bf159140"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "chat_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_chat_sessions_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_chat_sessions")),
    )
    op.create_index(op.f("ix_chat_sessions_user_id"), "chat_sessions", ["user_id"], unique=False)
    op.create_table(
        "checkins",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("mood", sa.SmallInteger(), nullable=False),
        sa.Column("energy", sa.SmallInteger(), nullable=False),
        sa.Column("sleep_hours", sa.Double(), nullable=True),
        sa.Column("note_enc", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_checkins_user_id_users"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_checkins")),
    )
    op.create_index(op.f("ix_checkins_created_at"), "checkins", ["created_at"], unique=False)
    op.create_index(op.f("ix_checkins_user_id"), "checkins", ["user_id"], unique=False)
    op.create_table(
        "chat_messages",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("content_enc", sa.Text(), nullable=False),
        sa.Column("emotion_label", sa.String(length=16), nullable=True),
        sa.Column("emotion_confidence", sa.Double(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["chat_sessions.id"],
            name=op.f("fk_chat_messages_session_id_chat_sessions"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_chat_messages")),
    )
    op.create_index(
        op.f("ix_chat_messages_created_at"), "chat_messages", ["created_at"], unique=False
    )
    op.create_index(
        op.f("ix_chat_messages_session_id"), "chat_messages", ["session_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_chat_messages_session_id"), table_name="chat_messages")
    op.drop_index(op.f("ix_chat_messages_created_at"), table_name="chat_messages")
    op.drop_table("chat_messages")
    op.drop_index(op.f("ix_checkins_user_id"), table_name="checkins")
    op.drop_index(op.f("ix_checkins_created_at"), table_name="checkins")
    op.drop_table("checkins")
    op.drop_index(op.f("ix_chat_sessions_user_id"), table_name="chat_sessions")
    op.drop_table("chat_sessions")
