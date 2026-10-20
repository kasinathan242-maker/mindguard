import logging
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel
from redis.exceptions import RedisError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.deps import RedisDep, SessionDep, SettingsDep

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])

CheckStatus = Literal["ok", "unavailable"]


class HealthChecks(BaseModel):
    database: CheckStatus
    redis: CheckStatus


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    version: str
    checks: HealthChecks


@router.get("/health")
async def health(session: SessionDep, redis: RedisDep, settings: SettingsDep) -> HealthResponse:
    database: CheckStatus = "ok"
    try:
        await session.execute(text("SELECT 1"))
    except (SQLAlchemyError, OSError):
        logger.warning("health check: database unavailable")
        database = "unavailable"

    cache: CheckStatus = "ok"
    try:
        await redis.ping()
    except (RedisError, OSError):
        logger.warning("health check: redis unavailable")
        cache = "unavailable"

    checks = HealthChecks(database=database, redis=cache)
    status = "ok" if database == "ok" and cache == "ok" else "degraded"
    return HealthResponse(status=status, version=settings.app_version, checks=checks)
