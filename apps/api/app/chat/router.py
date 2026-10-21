"""Chat: safety check -> prompt -> LLM -> output filter -> stream (Server-Sent Events).

Urgent messages never reach the LLM: the crisis event is streamed instead, and a content-free
safety_event is recorded. The assistant reply is fully generated and filtered before any of it is
streamed, so an unsafe reply can never be partially shown.
"""

import json
import uuid
from collections.abc import AsyncIterator, Callable
from datetime import timedelta
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import delete, select

from app.auth.models import User
from app.chat.models import ChatMessage, ChatSession
from app.chat.prompts import SAFE_FALLBACK, build_system_prompt
from app.chat.providers import (
    AnthropicProvider,
    CustomCompanionProvider,
    LLMProvider,
    MockProvider,
    OllamaProvider,
    Turn,
    strip_pii,
)
from app.checkins.models import Checkin
from app.consent.deps import require_consent
from app.consent.service import has_consent
from app.core.config import Settings
from app.core.crypto import decrypt, encrypt
from app.core.deps import SessionDep, SettingsDep
from app.core.rate_limit import rate_limit
from app.db.types import utcnow
from app.emotion.service import EmotionPredictor
from app.safety.engine import assess
from app.safety.rules import evaluate_rules
from app.safety.service import record_safety_event

router = APIRouter(prefix="/chat", tags=["chat"])

CoreUser = Annotated[User, Depends(require_consent("core"))]
ProviderFactory = Callable[[Settings, bool], LLMProvider]

# Categories that must never appear in an assistant reply.
_FORBIDDEN_REPLY_CATEGORIES = {"means", "method_seeking", "intent", "self_harm", "goodbye"}


def default_provider(settings: Settings, cloud_allowed: bool) -> LLMProvider:
    if settings.llm_provider in ("custom", "mock"):
        return CustomCompanionProvider()
    if settings.llm_provider == "ollama":
        return OllamaProvider(settings.ollama_base_url, settings.llm_model)
    if settings.llm_provider == "anthropic" and cloud_allowed and settings.anthropic_api_key:
        return AnthropicProvider(settings.anthropic_api_key.get_secret_value(), settings.llm_model)
    return CustomCompanionProvider()


def _chat_limit(request: Request) -> int:
    settings: Settings = request.app.state.settings
    return settings.chat_rate_limit_per_minute


class SessionOut(BaseModel):
    id: uuid.UUID
    stores_history: bool


class HistoryTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: Annotated[str, Field(max_length=4000)]


class MessageIn(BaseModel):
    content: Annotated[str, Field(min_length=1, max_length=4000)]
    # Used only without `chat_history` consent, when the server keeps nothing between turns.
    history: Annotated[list[HistoryTurn], Field(max_length=20)] = []


def _sse(event: str, data: dict[str, object]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def filter_reply(reply: str) -> tuple[str, bool]:
    """Re-run the safety rules on the assistant's reply; replace it if it breaks a rule."""
    result = evaluate_rules(reply)
    unsafe = any(
        hit.category in _FORBIDDEN_REPLY_CATEGORIES and hit.level == "urgent" for hit in result.hits
    )
    return (SAFE_FALLBACK, True) if unsafe else (reply, False)


async def _owned_session(session: SessionDep, user: User, session_id: uuid.UUID) -> ChatSession:
    chat = await session.get(ChatSession, session_id)
    if chat is None or chat.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")
    return chat


@router.post("/sessions", status_code=status.HTTP_201_CREATED)
async def create_session(user: CoreUser, session: SessionDep) -> SessionOut:
    chat = ChatSession(user_id=user.id)
    session.add(chat)
    await session.commit()
    return SessionOut(
        id=chat.id, stores_history=await has_consent(session, user.id, "chat_history")
    )


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(session_id: uuid.UUID, user: CoreUser, session: SessionDep) -> None:
    chat = await _owned_session(session, user, session_id)
    await session.execute(delete(ChatMessage).where(ChatMessage.session_id == chat.id))
    await session.delete(chat)
    await session.commit()


@router.post(
    "/sessions/{session_id}/messages",
    dependencies=[Depends(rate_limit("chat", _chat_limit))],
)
async def send_message(
    session_id: uuid.UUID,
    body: MessageIn,
    request: Request,
    user: CoreUser,
    session: SessionDep,
    settings: SettingsDep,
) -> StreamingResponse:
    chat = await _owned_session(session, user, session_id)
    stores_history = await has_consent(session, user.id, "chat_history")
    key = settings.field_encryption_key.get_secret_value()
    # Model inference is CPU-bound; keep it off the event loop.
    safety = await run_in_threadpool(assess, body.content)

    if safety.is_urgent:
        record_safety_event(
            session, user.id, source="chat", level="urgent", detector=safety.detector or "rules"
        )
        await session.commit()

        async def crisis() -> AsyncIterator[str]:
            yield _sse("safety", {"level": "urgent"})
            yield _sse("crisis", {})
            yield _sse("done", {})

        return StreamingResponse(crisis(), media_type="text/event-stream")

    elevated = safety.level == "elevated"
    if elevated:
        record_safety_event(
            session, user.id, source="chat", level="elevated", detector=safety.detector or "rules"
        )

    if stores_history:
        rows = await session.scalars(
            select(ChatMessage)
            .where(ChatMessage.session_id == chat.id, ChatMessage.role != "system_safety")
            .order_by(ChatMessage.created_at.desc())
            .limit(settings.chat_history_turns)
        )
        turns = [Turn(r.role, decrypt(r.content_enc, key)) for r in reversed(list(rows))]  # type: ignore[arg-type]
    else:
        turns = [Turn(t.role, t.content) for t in body.history[-settings.chat_history_turns :]]
    turns.append(Turn("user", body.content))

    recent_mood = await session.scalar(
        select(Checkin.mood).where(Checkin.user_id == user.id).order_by(Checkin.created_at.desc())
    )
    cloud_allowed = await has_consent(session, user.id, "cloud_llm")
    factory: ProviderFactory = request.app.state.provider_factory
    provider = factory(settings, cloud_allowed)
    if provider.name == "anthropic":
        turns = [Turn(t.role, strip_pii(t.content)) for t in turns]

    emotion_model: EmotionPredictor | None = request.app.state.emotion_model
    emotion = (
        await run_in_threadpool(emotion_model.predict, body.content) if emotion_model else None
    )
    system = build_system_prompt(
        elevated=elevated, recent_mood=recent_mood, emotion=emotion.label if emotion else None
    )
    parts = [part async for part in provider.stream(system, turns)]
    reply, replaced = filter_reply("".join(parts).strip())

    if stores_history:
        # Explicit, strictly increasing timestamps keep the pair in order when read back.
        now = utcnow()
        session.add(
            ChatMessage(
                session_id=chat.id,
                role="user",
                content_enc=encrypt(body.content, key),
                emotion_label=emotion.label if emotion else None,
                emotion_confidence=emotion.confidence if emotion else None,
                created_at=now,
            )
        )
        session.add(
            ChatMessage(
                session_id=chat.id,
                role="assistant",
                content_enc=encrypt(reply, key),
                created_at=now + timedelta(microseconds=1),
            )
        )
    await session.commit()

    async def events() -> AsyncIterator[str]:
        yield _sse("safety", {"level": safety.level})
        if emotion:
            yield _sse("emotion", {"label": emotion.label, "confidence": emotion.confidence})
        for word in reply.split(" "):
            yield _sse("token", {"text": word + " "})
        yield _sse("done", {"filtered": replaced})

    return StreamingResponse(events(), media_type="text/event-stream")
