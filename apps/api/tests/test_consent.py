from fastapi import APIRouter, Depends, FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.audit.models import AuditLog
from app.auth.models import User
from app.consent.deps import require_consent
from app.core.resources import Resources
from tests.helpers import start_anonymous


def _granted(body: dict[str, object]) -> dict[str, bool]:
    items = body["items"]
    assert isinstance(items, list)
    return {item["scope"]: item["granted"] for item in items}


async def test_new_users_have_core_on_and_optional_scopes_off(client: AsyncClient) -> None:
    await start_anonymous(client)

    body = (await client.get("/api/v1/consents")).json()

    assert body["current_version"] == "1"
    assert _granted(body) == {
        "core": True,
        "chat_history": False,
        "voice": False,
        "wearables": False,
        "cloud_llm": False,
        "reminders": False,
    }
    core = next(item for item in body["items"] if item["scope"] == "core")
    assert core["required"] is True
    assert core["granted_at"] is not None


async def test_grant_and_revoke_are_audited(app: FastAPI, client: AsyncClient) -> None:
    await start_anonymous(client)

    granted = await client.put("/api/v1/consents", json={"consents": {"voice": True}})
    assert _granted(granted.json())["voice"] is True

    revoked = await client.put("/api/v1/consents", json={"consents": {"voice": False}})
    voice = next(item for item in revoked.json()["items"] if item["scope"] == "voice")
    assert voice["granted"] is False
    assert voice["revoked_at"] is not None

    # Re-sending an unchanged value is not a new event.
    await client.put("/api/v1/consents", json={"consents": {"voice": False}})

    resources: Resources = app.state.resources
    async with resources.sessionmaker() as session:
        actions = (
            await session.scalars(select(AuditLog.action).order_by(AuditLog.created_at))
        ).all()
    assert actions == ["consent.grant.core", "consent.grant.voice", "consent.revoke.voice"]


async def test_core_cannot_be_revoked_and_unknown_scopes_are_rejected(client: AsyncClient) -> None:
    await start_anonymous(client)

    assert (
        await client.put("/api/v1/consents", json={"consents": {"core": False}})
    ).status_code == 422
    assert (
        await client.put("/api/v1/consents", json={"consents": {"location": True}})
    ).status_code == 422


async def test_consents_require_a_session(client: AsyncClient) -> None:
    assert (await client.get("/api/v1/consents")).status_code == 401


async def test_require_consent_blocks_until_scope_is_granted(app: FastAPI) -> None:
    probe = APIRouter()

    @probe.get("/api/v1/_probe")
    async def needs_voice(user: User = Depends(require_consent("voice"))) -> dict[str, str]:  # noqa: B008
        return {"user": str(user.id)}

    app.include_router(probe)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as c:
        await start_anonymous(c)
        blocked = await c.get("/api/v1/_probe")
        assert blocked.status_code == 403
        assert blocked.json()["detail"] == {"code": "consent_required", "scope": "voice"}

        await c.put("/api/v1/consents", json={"consents": {"voice": True}})
        assert (await c.get("/api/v1/_probe")).status_code == 200
