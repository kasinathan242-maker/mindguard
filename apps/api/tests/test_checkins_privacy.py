from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy import func, select

from app.audit.models import AuditLog
from app.checkins.models import Checkin
from app.core.resources import Resources
from app.db.models import Base
from tests.helpers import start_anonymous


async def test_checkin_round_trip_with_encrypted_note(app: FastAPI, client: AsyncClient) -> None:
    await start_anonymous(client)
    created = await client.post(
        "/api/v1/checkins", json={"mood": 3, "energy": 2, "sleep_hours": 6.5, "note": "busy day"}
    )
    assert created.status_code == 201
    assert created.json()["safety_level"] == "none"

    listed = (await client.get("/api/v1/checkins")).json()
    assert [(c["mood"], c["note"]) for c in listed] == [(3, "busy day")]

    resources: Resources = app.state.resources
    async with resources.sessionmaker() as session:
        row = (await session.scalars(select(Checkin))).one()
    assert row.note_enc is not None
    assert "busy day" not in row.note_enc


async def test_checkin_validation(client: AsyncClient) -> None:
    await start_anonymous(client)
    for payload in ({"mood": 0, "energy": 3}, {"mood": 3, "energy": 6}, {"mood": 3}):
        assert (await client.post("/api/v1/checkins", json=payload)).status_code == 422


async def test_urgent_note_is_flagged(client: AsyncClient) -> None:
    await start_anonymous(client)
    response = await client.post(
        "/api/v1/checkins", json={"mood": 1, "energy": 1, "note": "i want to end my life"}
    )
    assert response.json()["safety_level"] == "urgent"


async def test_export_contains_all_user_data(client: AsyncClient) -> None:
    await start_anonymous(client, {"core": True, "chat_history": True})
    await client.post("/api/v1/checkins", json={"mood": 4, "energy": 4, "note": "good walk"})
    await client.post("/api/v1/assessments/GAD7", json={"answers": [1] * 7})
    chat = (await client.post("/api/v1/chat/sessions")).json()["id"]
    await client.post(f"/api/v1/chat/sessions/{chat}/messages", json={"content": "hello"})

    response = await client.get("/api/v1/privacy/export")

    assert response.status_code == 200
    assert "attachment" in response.headers["content-disposition"]
    data = response.json()
    assert data["checkins"][0]["note"] == "good walk"
    assert data["assessments"][0]["total"] == 7
    assert data["chat_sessions"][0]["messages"][0]["content"] == "hello"
    assert {c["scope"] for c in data["consents"]} >= {"core", "chat_history"}


async def test_delete_leaves_no_user_rows(app: FastAPI, client: AsyncClient) -> None:
    await start_anonymous(client, {"core": True, "chat_history": True})
    await client.post("/api/v1/checkins", json={"mood": 2, "energy": 2, "note": "x"})
    await client.post("/api/v1/assessments/PHQ9", json={"answers": [0] * 8 + [1]})
    chat = (await client.post("/api/v1/chat/sessions")).json()["id"]
    await client.post(f"/api/v1/chat/sessions/{chat}/messages", json={"content": "hello"})

    assert (await client.request("DELETE", "/api/v1/privacy/account", json={})).status_code == 422
    response = await client.request("DELETE", "/api/v1/privacy/account", json={"confirm": "DELETE"})
    assert response.status_code == 200
    assert (await client.get("/api/v1/auth/me")).status_code == 401

    resources: Resources = app.state.resources
    async with resources.sessionmaker() as session:
        for table in Base.metadata.sorted_tables:
            count = await session.scalar(select(func.count()).select_from(table))
            if table.name == "audit_log":
                actions = (await session.scalars(select(AuditLog.action))).all()
                users = (await session.scalars(select(AuditLog.user_id))).all()
                assert "account.delete" in actions
                assert set(users) == {None}
            else:
                assert count == 0, f"{table.name} still has {count} rows"


async def test_retention_removes_old_chat_and_notes_only(app: FastAPI, client: AsyncClient) -> None:
    import uuid
    from datetime import timedelta

    from app.chat.models import ChatMessage, ChatSession
    from app.db.types import utcnow
    from app.privacy.retention import enforce_retention

    user_id = uuid.UUID((await start_anonymous(client))["id"])
    resources: Resources = app.state.resources
    now = utcnow()
    async with resources.sessionmaker() as session:
        chat = ChatSession(user_id=user_id)
        session.add(chat)
        await session.flush()
        session.add_all(
            [
                ChatMessage(
                    session_id=chat.id,
                    role="user",
                    content_enc="v1:x",
                    created_at=now - timedelta(days=31),
                ),
                ChatMessage(session_id=chat.id, role="user", content_enc="v1:y", created_at=now),
                Checkin(
                    user_id=user_id,
                    mood=3,
                    energy=3,
                    note_enc="v1:a",
                    created_at=now - timedelta(days=181),
                ),
                Checkin(user_id=user_id, mood=3, energy=3, note_enc="v1:b", created_at=now),
            ]
        )
        await session.commit()
        result = await enforce_retention(session, chat_days=30, note_days=180)
        assert (result.chat_messages_deleted, result.checkin_notes_cleared) == (1, 1)
        notes = sorted(str(n) for n in (await session.scalars(select(Checkin.note_enc))).all())
        assert notes == ["None", "v1:b"]
        assert len((await session.scalars(select(ChatMessage))).all()) == 1
