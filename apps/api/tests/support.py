from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from fakeredis import FakeAsyncRedis
from sqlalchemy import event
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.config import Settings
from app.core.resources import Resources
from app.db.models import Base  # importing models registers every table


def _enable_sqlite_foreign_keys(dbapi_connection: Any, _: Any) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


@asynccontextmanager
async def in_memory_resources(_: Settings) -> AsyncGenerator[Resources]:
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    event.listen(engine.sync_engine, "connect", _enable_sqlite_foreign_keys)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    redis = FakeAsyncRedis(decode_responses=True)
    try:
        yield Resources(
            engine=engine,
            sessionmaker=async_sessionmaker(engine, expire_on_commit=False),
            redis=redis,
        )
    finally:
        await redis.aclose()
        await engine.dispose()
