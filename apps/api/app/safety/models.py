import uuid
from datetime import datetime

from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import UTCDateTime, utcnow


class SafetyEvent(Base):
    """That the safety flow was triggered, and what was shown. Never the message content."""

    __tablename__ = "safety_events"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    source: Mapped[str] = mapped_column(String(16))  # chat | phq9_item9 | journal | checkin
    level: Mapped[str] = mapped_column(String(16))  # elevated | urgent
    detector: Mapped[str] = mapped_column(String(16))  # rules | classifier | both | questionnaire
    resources_shown: Mapped[list[str]] = mapped_column(JSON().with_variant(JSONB(), "postgresql"))
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
