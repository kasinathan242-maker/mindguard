"""Long-lived process resources (DB engine, Redis) created once per app lifespan."""

from collections.abc import AsyncGenerator, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from dataclasses import dataclass

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import Settings


@dataclass(frozen=True, slots=True)
class Resources:
    engine: AsyncEngine
    sessionmaker: async_sessionmaker[AsyncSession]
    redis: Redis


ResourcesFactory = Callable[[Settings], AbstractAsyncContextManager[Resources]]


@asynccontextmanager
async def default_resources(settings: Settings) -> AsyncGenerator[Resources]:
    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    redis = Redis.from_url(settings.redis_url, decode_responses=True)
    try:
        yield Resources(
            engine=engine,
            sessionmaker=async_sessionmaker(engine, expire_on_commit=False),
            redis=redis,
        )
    finally:
        await redis.aclose()
        await engine.dispose()
