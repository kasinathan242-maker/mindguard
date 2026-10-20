import json
from collections.abc import AsyncIterator

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy import select

from app.chat.models import ChatMessage
from app.chat.prompts import SAFE_FALLBACK
from app.chat.providers import MockProvider, Turn, strip_pii
from app.chat.router import filter_reply
from app.core.config import Settings
from app.core.crypto import decrypt, encrypt
from app.core.resources import Resources
from app.safety.models import SafetyEvent
from tests.helpers import start_anonymous

KEY = Settings().field_encryption_key.get_secret_value()


class SpyProvider:
    name = "spy"

    def __init__(self, reply: str = "I'm here with you.") -> None:
        self.calls: list[tuple[str, list[Turn]]] = []
        self.reply = reply

    async def stream(self, system: str, turns: list[Turn]) -> AsyncIterator[str]:
        self.calls.append((system, turns))
        yield self.reply


@pytest.fixture
def spy(app: FastAPI) -> SpyProvider:
    provider = SpyProvider()
    app.state.provider_factory = lambda settings, cloud: provider
    return provider


def events(body: str) -> list[tuple[str, dict[str, object]]]:
    out = []
    for block in body.strip().split("\n\n"):
        lines = dict(line.split(": ", 1) for line in block.splitlines())
        out.append((lines["event"], json.loads(lines["data"])))
    return out


def text_of(evts: list[tuple[str, dict[str, object]]]) -> str:
    return "".join(str(d["text"]) for e, d in evts if e == "token").strip()


async def new_chat(client: AsyncClient, consents: dict[str, bool] | None = None) -> str:
    await start_anonymous(client, consents)
    response = await client.post("/api/v1/chat/sessions")
    assert response.status_code == 201
    return str(response.json()["id"])


@pytest.mark.parametrize(
    "message",
    [
        "I want to kill myself",
        "எனக்கு சாகணும்",
        "enakku saaganum da",
        "how many sleeping pills would it take",
    ],
)
async def test_urgent_messages_never_reach_the_llm(
    app: FastAPI, client: AsyncClient, spy: SpyProvider, message: str
) -> None:
    chat = await new_chat(client)

    response = await client.post(
        f"/api/v1/chat/sessions/{chat}/messages", json={"content": message}
    )

    assert response.status_code == 200
    evts = events(response.text)
    assert ("safety", {"level": "urgent"}) in evts
    assert any(e == "crisis" for e, _ in evts)
    assert not any(e == "token" for e, _ in evts)
    assert spy.calls == []
    resources: Resources = app.state.resources
    async with resources.sessionmaker() as session:
        event = (await session.scalars(select(SafetyEvent))).one()
    assert (event.source, event.level) == ("chat", "urgent")


async def test_normal_message_streams_the_reply(client: AsyncClient, spy: SpyProvider) -> None:
    chat = await new_chat(client)
    response = await client.post(
        f"/api/v1/chat/sessions/{chat}/messages", json={"content": "had a long day at college"}
    )
    evts = events(response.text)
    assert evts[0] == ("safety", {"level": "none"})
    assert text_of(evts) == "I'm here with you."
    assert len(spy.calls) == 1
    system, turns = spy.calls[0]
    assert "Never diagnose" in system
    assert "Safety mode" not in system
    assert turns[-1] == Turn("user", "had a long day at college")


async def test_elevated_message_uses_the_safety_prompt(
    client: AsyncClient, spy: SpyProvider
) -> None:
    chat = await new_chat(client)
    response = await client.post(
        f"/api/v1/chat/sessions/{chat}/messages", json={"content": "everything feels hopeless"}
    )
    assert events(response.text)[0] == ("safety", {"level": "elevated"})
    assert "Safety mode is on" in spy.calls[0][0]


async def test_unsafe_assistant_replies_are_replaced(app: FastAPI, client: AsyncClient) -> None:
    bad = SpyProvider("The easiest way to die is something I can describe.")
    app.state.provider_factory = lambda settings, cloud: bad
    chat = await new_chat(client)
    response = await client.post(
        f"/api/v1/chat/sessions/{chat}/messages", json={"content": "tell me something"}
    )
    evts = events(response.text)
    assert text_of(evts) == SAFE_FALLBACK
    assert evts[-1] == ("done", {"filtered": True})


def test_filter_reply_keeps_supportive_text() -> None:
    assert filter_reply("Thank you for sharing. Tele-MANAS (14416) is free and open 24x7.") == (
        "Thank you for sharing. Tele-MANAS (14416) is free and open 24x7.",
        False,
    )


async def test_history_is_stored_encrypted_only_with_consent(
    app: FastAPI, client: AsyncClient, spy: SpyProvider
) -> None:
    resources: Resources = app.state.resources
    chat = await new_chat(client, {"core": True, "chat_history": True})
    await client.post(f"/api/v1/chat/sessions/{chat}/messages", json={"content": "feeling okay"})
    await client.post(f"/api/v1/chat/sessions/{chat}/messages", json={"content": "and you?"})

    async with resources.sessionmaker() as session:
        rows = (await session.scalars(select(ChatMessage).order_by(ChatMessage.created_at))).all()
    assert [r.role for r in rows] == ["user", "assistant", "user", "assistant"]
    assert all(r.content_enc.startswith("v1:") for r in rows)
    assert "feeling okay" not in rows[0].content_enc
    assert decrypt(rows[0].content_enc, KEY) == "feeling okay"
    # The second call received the stored first turn as context.
    assert [t.content for t in spy.calls[1][1]] == [
        "feeling okay",
        "I'm here with you.",
        "and you?",
    ]


async def test_without_consent_nothing_is_stored(
    app: FastAPI, client: AsyncClient, spy: SpyProvider
) -> None:
    chat = await new_chat(client)
    await client.post(
        f"/api/v1/chat/sessions/{chat}/messages",
        json={"content": "second", "history": [{"role": "user", "content": "first"}]},
    )
    resources: Resources = app.state.resources
    async with resources.sessionmaker() as session:
        assert (await session.scalars(select(ChatMessage))).all() == []
    assert [t.content for t in spy.calls[0][1]] == ["first", "second"]


async def test_chats_are_private_and_deletable(client: AsyncClient, app: FastAPI) -> None:
    from httpx import ASGITransport

    chat = await new_chat(client)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as other:
        await start_anonymous(other)
        stolen = await other.post(f"/api/v1/chat/sessions/{chat}/messages", json={"content": "hi"})
        assert stolen.status_code == 404
    assert (await client.delete(f"/api/v1/chat/sessions/{chat}")).status_code == 204
    gone = await client.post(f"/api/v1/chat/sessions/{chat}/messages", json={"content": "hi"})
    assert gone.status_code == 404


async def test_mock_provider_is_supportive_and_offline() -> None:
    parts = [p async for p in MockProvider().stream("base", [Turn("user", "I feel anxious")])]
    assert "breathe" in "".join(parts)


def test_pii_is_stripped_before_cloud_calls() -> None:
    cleaned = strip_pii("My name is Priya, mail priya@example.in or call 98765 43210")
    assert "Priya" not in cleaned
    assert "priya@example.in" not in cleaned
    assert "98765" not in cleaned


def test_field_encryption_round_trip_and_randomness() -> None:
    first, second = encrypt("note", KEY), encrypt("note", KEY)
    assert first != second
    assert decrypt(first, KEY) == "note"
