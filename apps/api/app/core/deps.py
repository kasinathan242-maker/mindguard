from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.resources import Resources


def get_resources(request: Request) -> Resources:
    resources: Resources = request.app.state.resources
    return resources


def get_app_settings(request: Request) -> Settings:
    settings: Settings = request.app.state.settings
    return settings


async def get_session(
    resources: Annotated[Resources, Depends(get_resources)],
) -> AsyncIterator[AsyncSession]:
    async with resources.sessionmaker() as session:
        yield session


def get_redis(resources: Annotated[Resources, Depends(get_resources)]) -> Redis:
    return resources.redis


SessionDep = Annotated[AsyncSession, Depends(get_session)]
RedisDep = Annotated[Redis, Depends(get_redis)]
SettingsDep = Annotated[Settings, Depends(get_app_settings)]
