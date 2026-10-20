"""Create a demo account with 60 days of SYNTHETIC data, for demos only.

    uv run python -m app.demo_seed
    docker compose exec api python -m app.demo_seed   # inside the Compose stack

Sign in with demo@mindguard.example / "demo account only". Every check-in note says it is
synthetic. Refuses to run when APP_ENV=production.
"""

import asyncio
import random
from datetime import timedelta

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.assessments.instruments import GAD7, PHQ9
from app.assessments.models import Assessment
from app.assessments.scoring import score
from app.auth.models import User
from app.checkins.models import Checkin
from app.consent.service import apply_consents
from app.core.config import Settings, get_settings
from app.core.crypto import encrypt
from app.core.security import hash_password
from app.db.types import utcnow

DEMO_EMAIL = "demo@mindguard.example"
DEMO_PASSWORD = "demo account only"  # noqa: S105 - published on purpose for demos
DAYS = 60
NOTES = [
    "Synthetic demo note: busy day of classes.",
    "Synthetic demo note: slept late, felt tired.",
    "Synthetic demo note: good talk with a friend.",
    "Synthetic demo note: exam prep was stressful.",
]


async def seed(session: AsyncSession, settings: Settings, rng: random.Random) -> User:
    await session.execute(delete(User).where(User.email == DEMO_EMAIL))
    user = User(
        is_anonymous=False,
        email=DEMO_EMAIL,
        password_hash=hash_password(DEMO_PASSWORD),
        locale="en",
        created_at=utcnow() - timedelta(days=DAYS),
    )
    session.add(user)
    await session.flush()
    await apply_consents(session, user.id, {"core": True, "chat_history": True})

    key = settings.field_encryption_key.get_secret_value()
    now = utcnow()
    for day in range(DAYS, 0, -1):
        # A gentle improving trend with weekday noise, so charts have something to show.
        base = 2.4 + (DAYS - day) / DAYS * 1.4
        mood = max(1, min(5, round(base + rng.uniform(-1, 1))))
        energy = max(1, min(5, round(base + rng.uniform(-1.2, 0.8))))
        sleep = round(rng.uniform(5, 8.5) * 2) / 2
        note = rng.choice(NOTES) if day % 5 == 0 else None
        session.add(
            Checkin(
                user_id=user.id,
                mood=mood,
                energy=energy,
                sleep_hours=sleep,
                note_enc=encrypt(note, key) if note else None,
                created_at=now - timedelta(days=day, hours=rng.randint(0, 4)),
            )
        )
    for weeks_ago, level in ((8, 2), (6, 2), (4, 1), (2, 1), (0, 1)):
        for instrument in (PHQ9, GAD7):
            answers = [min(3, max(0, level + rng.choice((-1, 0, 0, 1)))) for _ in instrument.items]
            if instrument.safety_item is not None:
                answers[instrument.safety_item] = 0
            result = score(instrument, answers)
            session.add(
                Assessment(
                    user_id=user.id,
                    type=instrument.type,
                    answers=answers,
                    total=result.total,
                    severity_band=result.band,
                    safety_item_positive=False,
                    created_at=now - timedelta(weeks=weeks_ago, days=1),
                )
            )
    await session.commit()
    return user


async def _main() -> None:
    settings = get_settings()
    if settings.is_production:
        raise SystemExit("refusing to seed demo data in production")
    engine = create_async_engine(settings.database_url)
    async with async_sessionmaker(engine)() as session:
        await seed(session, settings, random.Random(2026))  # noqa: S311 - not security sensitive
        count = len((await session.scalars(select(Checkin))).all())
    await engine.dispose()
    print(f"demo account ready: {DEMO_EMAIL} / {DEMO_PASSWORD!r} ({count} check-ins in database)")


if __name__ == "__main__":
    asyncio.run(_main())
