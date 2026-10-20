"""Data export and permanent account deletion (DPDP Act: access and erasure)."""

import json
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import select

from app.assessments.models import Assessment
from app.audit.models import AuditLog
from app.audit.service import record
from app.auth.deps import ACCESS_COOKIE, REFRESH_COOKIE, CurrentUser
from app.chat.models import ChatMessage, ChatSession
from app.checkins.models import Checkin
from app.consent.models import Consent
from app.core.crypto import decrypt
from app.core.deps import SessionDep, SettingsDep
from app.integrations.wearables import WearableSample
from app.safety.models import SafetyEvent

router = APIRouter(prefix="/privacy", tags=["privacy"])


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


@router.get("/export")
async def export(user: CurrentUser, session: SessionDep, settings: SettingsDep) -> Response:
    """Everything stored about the user, decrypted, as one JSON file."""
    key = settings.field_encryption_key.get_secret_value()
    uid = user.id
    consents = (await session.scalars(select(Consent).where(Consent.user_id == uid))).all()
    assessments = (await session.scalars(select(Assessment).where(Assessment.user_id == uid))).all()
    checkins = (await session.scalars(select(Checkin).where(Checkin.user_id == uid))).all()
    chats = (await session.scalars(select(ChatSession).where(ChatSession.user_id == uid))).all()
    events = (await session.scalars(select(SafetyEvent).where(SafetyEvent.user_id == uid))).all()
    audit = (await session.scalars(select(AuditLog).where(AuditLog.user_id == uid))).all()
    wearables = (
        await session.scalars(select(WearableSample).where(WearableSample.user_id == uid))
    ).all()

    chat_out = []
    for chat in chats:
        messages = await session.scalars(
            select(ChatMessage)
            .where(ChatMessage.session_id == chat.id)
            .order_by(ChatMessage.created_at)
        )
        chat_out.append(
            {
                "id": str(chat.id),
                "created_at": _iso(chat.created_at),
                "messages": [
                    {
                        "role": m.role,
                        "content": decrypt(m.content_enc, key),
                        "created_at": _iso(m.created_at),
                    }
                    for m in messages
                ],
            }
        )

    data = {
        "exported_at": datetime.now().astimezone().isoformat(),
        "user": {
            "id": str(uid),
            "is_anonymous": user.is_anonymous,
            "email": user.email,
            "locale": user.locale,
            "created_at": _iso(user.created_at),
        },
        "consents": [
            {
                "scope": c.scope,
                "granted": c.granted,
                "version": c.version,
                "granted_at": _iso(c.granted_at),
                "revoked_at": _iso(c.revoked_at),
            }
            for c in consents
        ],
        "assessments": [
            {
                "type": a.type,
                "answers": list(a.answers),
                "total": a.total,
                "severity_band": a.severity_band,
                "functional_difficulty": a.functional_difficulty,
                "created_at": _iso(a.created_at),
            }
            for a in assessments
        ],
        "checkins": [
            {
                "mood": c.mood,
                "energy": c.energy,
                "sleep_hours": c.sleep_hours,
                "note": decrypt(c.note_enc, key) if c.note_enc else None,
                "created_at": _iso(c.created_at),
            }
            for c in checkins
        ],
        "chat_sessions": chat_out,
        "safety_events": [
            {
                "source": e.source,
                "level": e.level,
                "detector": e.detector,
                "resources_shown": e.resources_shown,
                "created_at": _iso(e.created_at),
            }
            for e in events
        ],
        "wearables": [
            {"day": s.day.isoformat(), "metric": s.metric, "value": s.value, "source": s.source}
            for s in wearables
        ],
        "audit_log": [{"action": a.action, "created_at": _iso(a.created_at)} for a in audit],
    }
    record(session, uid, "privacy.export")
    await session.commit()
    return Response(
        content=json.dumps(data, ensure_ascii=False, indent=2),
        media_type="application/json",
        headers={"Content-Disposition": 'attachment; filename="mindguard-export.json"'},
    )


class DeleteAccount(BaseModel):
    confirm: Literal["DELETE"]


@router.delete("/account")
async def delete_account(
    body: DeleteAccount, user: CurrentUser, session: SessionDep, settings: SettingsDep
) -> JSONResponse:
    """Hard delete: every row tied to the user cascades away; an anonymous audit entry stays."""
    await session.delete(user)
    record(session, None, "account.delete")
    await session.commit()
    response = JSONResponse(status_code=status.HTTP_200_OK, content={"deleted": True})
    for name, path in ((ACCESS_COOKIE, "/api"), (REFRESH_COOKIE, "/api/v1/auth")):
        response.delete_cookie(
            name, path=path, httponly=True, secure=settings.cookie_secure, samesite="strict"
        )
    return response
