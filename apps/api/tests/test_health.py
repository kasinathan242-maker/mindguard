import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from redis.exceptions import ConnectionError as RedisConnectionError

from app.core.resources import Resources


async def test_health_reports_ok_when_dependencies_respond(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "version": "0.1.0",
        "checks": {"database": "ok", "redis": "ok"},
    }


async def test_health_degrades_when_redis_is_down(
    app: FastAPI, client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    resources: Resources = app.state.resources

    async def failing_ping() -> bool:
        raise RedisConnectionError("down")

    monkeypatch.setattr(resources.redis, "ping", failing_ping)

    response = await client.get("/api/v1/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "degraded"
    assert body["checks"] == {"database": "ok", "redis": "unavailable"}


async def test_api_docs_are_hidden_in_production() -> None:
    from app.core.config import Settings
    from app.main import create_app

    prod = create_app(Settings(app_env="production"))
    paths = {getattr(route, "path", "") for route in prod.routes}

    assert "/api/docs" not in paths
    assert "/api/openapi.json" not in paths
