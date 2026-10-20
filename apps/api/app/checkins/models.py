import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, SmallInteger, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import UTCDateTime, utcnow


class Checkin(Base):
    __tablename__ = "checkins"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    mood: Mapped[int] = mapped_column(SmallInteger)  # 1-5
    energy: Mapped[int] = mapped_column(SmallInteger)  # 1-5
    sleep_hours: Mapped[float | None]
    note_enc: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow, index=True)
