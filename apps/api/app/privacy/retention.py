"""Retention: chat messages are kept 30 days and check-in notes 180 days (configurable).

Run daily, e.g. from cron or a scheduled container:

    uv run python -m app.privacy.retention
"""

import asyncio
from dataclasses import dataclass
from datetime import timedelta

from sqlalchemy import delete, update
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.chat.models import ChatMessage
from app.checkins.models import Checkin
from app.core.config import get_settings
from app.db.types import utcnow


@dataclass(frozen=True, slots=True)
class RetentionResult:
    chat_messages_deleted: int
    checkin_notes_cleared: int


async def enforce_retention(
    session: AsyncSession, *, chat_days: int, note_days: int
) -> RetentionResult:
    now = utcnow()
    chats = await session.execute(
        delete(ChatMessage).where(ChatMessage.created_at < now - timedelta(days=chat_days))
    )
    notes = await session.execute(
        update(Checkin)
        .where(Checkin.note_enc.is_not(None), Checkin.created_at < now - timedelta(days=note_days))
        .values(note_enc=None)
    )
    await session.commit()
    return RetentionResult(
        chat_messages_deleted=chats.rowcount or 0,  # type: ignore[attr-defined]
        checkin_notes_cleared=notes.rowcount or 0,  # type: ignore[attr-defined]
    )


async def _main() -> None:
    settings = get_settings()
    engine = create_async_engine(settings.database_url)
    async with AsyncSession(engine) as session:
        result = await enforce_retention(
            session,
            chat_days=settings.retention_chat_days,
            note_days=settings.retention_note_days,
        )
    await engine.dispose()
    print(result)


if __name__ == "__main__":
    asyncio.run(_main())
