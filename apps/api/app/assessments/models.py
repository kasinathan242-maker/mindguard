import uuid
from datetime import datetime

from sqlalchemy import JSON, ForeignKey, Integer, SmallInteger, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import UTCDateTime, utcnow


class Assessment(Base):
    __tablename__ = "assessments"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    type: Mapped[str] = mapped_column(String(8))
    answers: Mapped[list[int]] = mapped_column(
        JSON().with_variant(ARRAY(SmallInteger()), "postgresql")
    )
    total: Mapped[int] = mapped_column(Integer)
    severity_band: Mapped[str] = mapped_column(String(24))
    safety_item_positive: Mapped[bool]
    # Unscored "how difficult have these problems made it..." answer (0-3), when given.
    functional_difficulty: Mapped[int | None] = mapped_column(SmallInteger)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow, index=True)
