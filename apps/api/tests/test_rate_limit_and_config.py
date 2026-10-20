import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from pydantic import SecretStr, ValidationError

from app.core.config import Settings
from app.main import create_app
from tests.support import in_memory_resources


async def test_auth_endpoints_are_rate_limited(settings: Settings) -> None:
    limited = settings.model_copy(update={"auth_rate_limit_per_minute": 3})
    app = create_app(limited, resources_factory=in_memory_resources)
    payload = {"email": "x@example.in", "password": "wrong password"}

    async with (
        LifespanManager(app),
        AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client,
    ):
        statuses = [
            (await client.post("/api/v1/auth/login", json=payload)).status_code for _ in range(4)
        ]
        blocked = await client.post("/api/v1/auth/login", json=payload)
        me = await client.get("/api/v1/auth/me")

    assert statuses == [401, 401, 401, 429]
    assert blocked.status_code == 429
    assert int(blocked.headers["retry-after"]) > 0
    assert me.status_code == 401  # session reads are not throttled


def test_production_refuses_the_development_jwt_secret() -> None:
    with pytest.raises(ValidationError, match="JWT_SECRET"):
        Settings(app_env="production", cookie_secure=True)


def test_production_requires_secure_cookies() -> None:
    with pytest.raises(ValidationError, match="COOKIE_SECURE"):
        Settings(
            app_env="production",
            jwt_secret=SecretStr("x" * 48),
            field_encryption_key=SecretStr("A" * 43 + "="),
            cookie_secure=False,
        )


def test_production_accepts_hardened_settings() -> None:
    settings = Settings(
        app_env="production",
        jwt_secret=SecretStr("x" * 48),
        field_encryption_key=SecretStr("A" * 43 + "="),
        cookie_secure=True,
    )
    assert settings.is_production
