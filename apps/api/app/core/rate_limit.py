"""Fixed-window rate limiting backed by Redis.

Clients are keyed by a truncated hash of their IP, so raw addresses never land in Redis.
If Redis is unreachable the limiter fails open and logs, because locking every user out of
sign-in (or out of a crisis resource) is worse than briefly losing throttling.
"""

import hashlib
import logging
import time
from collections.abc import Awaitable, Callable

from fastapi import HTTPException, Request, status
from redis.exceptions import RedisError

from app.core.deps import RedisDep

logger = logging.getLogger(__name__)


def _client_key(request: Request) -> str:
    host = request.client.host if request.client else "unknown"
    return hashlib.sha256(host.encode()).hexdigest()[:16]


def rate_limit(
    bucket: str, limit: Callable[[Request], int] | int, window_s: int = 60
) -> Callable[[Request, RedisDep], Awaitable[None]]:
    async def dependency(request: Request, redis: RedisDep) -> None:
        max_hits = limit(request) if callable(limit) else limit
        window = int(time.time() // window_s)
        key = f"rl:{bucket}:{_client_key(request)}:{window}"
        try:
            hits = await redis.incr(key)
            if hits == 1:
                await redis.expire(key, window_s)
        except RedisError:
            logger.warning("rate limiter unavailable; allowing request", extra={"bucket": bucket})
            return
        if hits > max_hits:
            retry_after = window_s - int(time.time()) % window_s
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please wait a moment and try again.",
                headers={"Retry-After": str(retry_after)},
            )

    return dependency
