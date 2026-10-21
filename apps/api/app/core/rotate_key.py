"""Re-encrypt every encrypted field with a new key.

    OLD_FIELD_ENCRYPTION_KEY=... NEW_FIELD_ENCRYPTION_KEY=... uv run python -m app.core.rotate_key

Run with the API stopped (or in maintenance), then set FIELD_ENCRYPTION_KEY to the new key and
start the API. The rotation runs in one transaction: either every value is re-encrypted, or none is.
"""

import asyncio
import os

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.chat.models import ChatMessage
from app.checkins.models import Checkin
from app.core.config import get_settings
from app.core.crypto import decrypt, encrypt


async def rotate(session: AsyncSession, old_key: str, new_key: str) -> int:
    """Re-encrypt all chat messages and check-in notes. Returns how many values changed."""
    encrypt("check", new_key)  # fail fast on a malformed new key, before touching any row
    changed = 0
    for message in await session.scalars(select(ChatMessage)):
        message.content_enc = encrypt(decrypt(message.content_enc, old_key), new_key)
        changed += 1
    for checkin in await session.scalars(select(Checkin).where(Checkin.note_enc.is_not(None))):
        assert checkin.note_enc is not None
        checkin.note_enc = encrypt(decrypt(checkin.note_enc, old_key), new_key)
        changed += 1
    await session.commit()
    return changed


async def _main() -> None:
    old_key = os.environ["OLD_FIELD_ENCRYPTION_KEY"]
    new_key = os.environ["NEW_FIELD_ENCRYPTION_KEY"]
    engine = create_async_engine(get_settings().database_url)
    async with async_sessionmaker(engine)() as session:
        count = await rotate(session, old_key, new_key)
    await engine.dispose()
    print(f"re-encrypted {count} values; now set FIELD_ENCRYPTION_KEY to the new key")


if __name__ == "__main__":
    asyncio.run(_main())
