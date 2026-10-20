import uuid
from datetime import timedelta

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.audit.models import AuditLog
from app.auth.models import RefreshToken
from app.core.resources import Resources
from app.core.security import create_access_token
from tests.helpers import register, start_anonymous


def _set_cookie_headers(headers: list[str], name: str) -> str:
    return next(h for h in headers if h.startswith(f"{name}="))


async def test_anonymous_start_sets_hardened_cookies_and_returns_user(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/anonymous",
        json={"age_confirmed": True, "locale": "ta", "consents": {"core": True}},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["is_anonymous"] is True
    assert body["email"] is None
    assert body["locale"] == "ta"

    cookies = response.headers.get_list("set-cookie")
    access = _set_cookie_headers(cookies, "mg_access").lower()
    refresh = _set_cookie_headers(cookies, "mg_refresh").lower()
    for header in (access, refresh):
        assert "httponly" in header
        assert "samesite=strict" in header
    assert "path=/api;" in access
    assert "path=/api/v1/auth" in refresh

    me = await client.get("/api/v1/auth/me")
    assert me.status_code == 200
    assert me.json()["id"] == body["id"]


@pytest.mark.parametrize(
    "payload",
    [
        {"age_confirmed": False, "consents": {"core": True}},
        {"consents": {"core": True}},
        {"age_confirmed": True, "consents": {"core": False}},
        {"age_confirmed": True, "consents": {}},
        {"age_confirmed": True, "consents": {"core": True}, "locale": "fr"},
    ],
)
async def test_anonymous_start_requires_adult_and_core_consent(
    client: AsyncClient, payload: dict[str, object]
) -> None:
    response = await client.post("/api/v1/auth/anonymous", json=payload)
    assert response.status_code == 422


async def test_me_requires_a_valid_session(client: AsyncClient) -> None:
    assert (await client.get("/api/v1/auth/me")).status_code == 401

    client.cookies.set("mg_access", "not-a-jwt", path="/api")
    assert (await client.get("/api/v1/auth/me")).status_code == 401


async def test_expired_or_foreign_tokens_are_rejected(client: AsyncClient) -> None:
    user = await start_anonymous(client)
    user_id = uuid.UUID(user["id"])

    client.cookies.clear()
    expired = create_access_token(
        user_id, "dev-only-insecure-jwt-secret-do-not-use-in-production", timedelta(seconds=-1)
    )
    client.cookies.set("mg_access", expired, path="/api")
    assert (await client.get("/api/v1/auth/me")).status_code == 401

    client.cookies.clear()
    forged = create_access_token(
        user_id, "some-other-secret-of-sufficient-length", timedelta(minutes=5)
    )
    client.cookies.set("mg_access", forged, path="/api")
    assert (await client.get("/api/v1/auth/me")).status_code == 401


async def test_register_login_and_generic_failure_message(client: AsyncClient) -> None:
    created = await register(client, email="  Asha@Example.IN ")
    assert created.status_code == 201
    assert created.json()["email"] == "asha@example.in"
    assert created.json()["is_anonymous"] is False

    client.cookies.clear()
    ok = await client.post(
        "/api/v1/auth/login",
        json={"email": "asha@example.in", "password": "correct horse battery"},
    )
    assert ok.status_code == 200

    wrong_password = await client.post(
        "/api/v1/auth/login", json={"email": "asha@example.in", "password": "nope nope nope"}
    )
    unknown_email = await client.post(
        "/api/v1/auth/login", json={"email": "nobody@example.in", "password": "nope nope nope"}
    )
    assert wrong_password.status_code == unknown_email.status_code == 401
    assert wrong_password.json() == unknown_email.json()


async def test_register_rejects_duplicates_and_weak_passwords(client: AsyncClient) -> None:
    assert (await register(client)).status_code == 201
    assert (await register(client)).status_code == 409
    assert (await register(client, email="new@example.in", password="short")).status_code == 422


async def test_upgrade_keeps_the_same_account_and_its_consents(
    app: FastAPI, client: AsyncClient
) -> None:
    anon = await start_anonymous(client, consents={"core": True, "chat_history": True})

    upgraded = await client.post(
        "/api/v1/auth/upgrade", json={"email": "kavin@example.in", "password": "a long passphrase"}
    )

    assert upgraded.status_code == 200
    assert upgraded.json()["id"] == anon["id"]
    assert upgraded.json()["is_anonymous"] is False

    consents = (await client.get("/api/v1/consents")).json()["items"]
    assert {c["scope"]: c["granted"] for c in consents}["chat_history"] is True

    again = await client.post(
        "/api/v1/auth/upgrade", json={"email": "other@example.in", "password": "a long passphrase"}
    )
    assert again.status_code == 409

    client.cookies.clear()
    login = await client.post(
        "/api/v1/auth/login", json={"email": "kavin@example.in", "password": "a long passphrase"}
    )
    assert login.json()["id"] == anon["id"]

    resources: Resources = app.state.resources
    async with resources.sessionmaker() as session:
        actions = (await session.scalars(select(AuditLog.action))).all()
    assert "account.upgrade" in actions


async def test_upgrade_rejects_an_email_already_in_use(client: AsyncClient) -> None:
    await register(client, email="taken@example.in")
    client.cookies.clear()
    await start_anonymous(client)

    response = await client.post(
        "/api/v1/auth/upgrade", json={"email": "taken@example.in", "password": "a long passphrase"}
    )
    assert response.status_code == 409


async def test_refresh_rotates_and_detects_token_reuse(app: FastAPI, client: AsyncClient) -> None:
    await start_anonymous(client)
    original = client.cookies.get("mg_refresh")
    assert original

    rotated = await client.post("/api/v1/auth/refresh")
    assert rotated.status_code == 200
    current = client.cookies.get("mg_refresh")
    assert current
    assert current != original

    # An attacker replays the old token from a different client.
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as other:
        other.cookies.set("mg_refresh", original, path="/api/v1/auth")
        replay = await other.post("/api/v1/auth/refresh")
    assert replay.status_code == 401

    # The whole family is now revoked, so the legitimate holder must sign in again.
    after = await client.post("/api/v1/auth/refresh")
    assert after.status_code == 401
    assert "mg_refresh=" in after.headers.get("set-cookie", "")

    resources: Resources = app.state.resources
    async with resources.sessionmaker() as session:
        live = (
            await session.scalars(select(RefreshToken).where(RefreshToken.revoked_at.is_(None)))
        ).all()
    assert live == []


async def test_refresh_without_cookie_is_rejected(client: AsyncClient) -> None:
    assert (await client.post("/api/v1/auth/refresh")).status_code == 401


async def test_logout_revokes_refresh_token_and_clears_cookies(client: AsyncClient) -> None:
    await start_anonymous(client)
    token = client.cookies.get("mg_refresh")

    response = await client.post("/api/v1/auth/logout")
    assert response.status_code == 204
    assert client.cookies.get("mg_access") is None

    client.cookies.set("mg_refresh", token or "", path="/api/v1/auth")
    assert (await client.post("/api/v1/auth/refresh")).status_code == 401


async def test_locale_can_be_changed(client: AsyncClient) -> None:
    await start_anonymous(client)
    response = await client.put("/api/v1/auth/me/locale", json={"locale": "ta"})
    assert response.json()["locale"] == "ta"
