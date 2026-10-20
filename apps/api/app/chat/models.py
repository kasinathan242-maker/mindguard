import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import UTCDateTime, utcnow


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
    ended_at: Mapped[datetime | None] = mapped_column(UTCDateTime)


class ChatMessage(Base):
    """Stored only when the user has granted `chat_history`. Content is AES-GCM encrypted."""

    __tablename__ = "chat_messages"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("chat_sessions.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[str] = mapped_column(String(16))  # user | assistant | system_safety
    content_enc: Mapped[str] = mapped_column(Text)
    emotion_label: Mapped[str | None] = mapped_column(String(16))
    emotion_confidence: Mapped[float | None]
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow, index=True)
