from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import pytest
from asgi_lifespan import LifespanManager
from fakeredis import FakeAsyncRedis
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.config import Settings
from app.core.resources import Resources
from app.db.models import Base  # importing models registers every table
from app.main import create_app


@pytest.fixture
def settings() -> Settings:
    return Settings(
        app_env="test",
        database_url="sqlite+aiosqlite://",
        redis_url="redis://unused",
        cors_origins=["http://testserver"],
    )


@asynccontextmanager
async def in_memory_resources(_: Settings) -> AsyncGenerator[Resources]:
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
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


@pytest.fixture
async def app(settings: Settings) -> AsyncGenerator[FastAPI]:
    application = create_app(settings, resources_factory=in_memory_resources)
    async with LifespanManager(application):
        yield application


@pytest.fixture
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as c:
        yield c
