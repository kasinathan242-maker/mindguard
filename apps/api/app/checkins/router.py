import uuid
from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query, status
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.auth.models import User
from app.checkins.models import Checkin
from app.consent.deps import require_consent
from app.core.crypto import decrypt, encrypt
from app.core.deps import SessionDep, SettingsDep
from app.safety.engine import assess
from app.safety.service import record_safety_event

router = APIRouter(prefix="/checkins", tags=["checkins"])

CoreUser = Annotated[User, Depends(require_consent("core"))]
Scale = Annotated[int, Field(ge=1, le=5)]


class CheckinIn(BaseModel):
    mood: Scale
    energy: Scale
    sleep_hours: Annotated[float | None, Field(ge=0, le=24)] = None
    note: Annotated[str | None, Field(max_length=2000)] = None


class CheckinOut(BaseModel):
    id: uuid.UUID
    mood: int
    energy: int
    sleep_hours: float | None
    note: str | None
    created_at: datetime


class CheckinCreated(CheckinOut):
    # The note passed through the safety engine; the client shows the crisis card when urgent.
    safety_level: Literal["none", "elevated", "urgent"]


def _out(row: Checkin, key: str) -> CheckinOut:
    return CheckinOut(
        id=row.id,
        mood=row.mood,
        energy=row.energy,
        sleep_hours=row.sleep_hours,
        note=decrypt(row.note_enc, key) if row.note_enc else None,
        created_at=row.created_at,
    )


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_checkin(
    body: CheckinIn, user: CoreUser, session: SessionDep, settings: SettingsDep
) -> CheckinCreated:
    key = settings.field_encryption_key.get_secret_value()
    note = (body.note or "").strip() or None
    level: Literal["none", "elevated", "urgent"] = "none"
    if note:
        safety = await run_in_threadpool(assess, note)
        level = safety.level
        if level != "none":
            record_safety_event(
                session, user.id, source="checkin", level=level, detector=safety.detector or "rules"
            )
    row = Checkin(
        user_id=user.id,
        mood=body.mood,
        energy=body.energy,
        sleep_hours=body.sleep_hours,
        note_enc=encrypt(note, key) if note else None,
    )
    session.add(row)
    await session.commit()
    return CheckinCreated(**_out(row, key).model_dump(), safety_level=level)


@router.get("")
async def list_checkins(
    user: CoreUser,
    session: SessionDep,
    settings: SettingsDep,
    since: Annotated[datetime | None, Query(alias="from")] = None,
    until: Annotated[datetime | None, Query(alias="to")] = None,
) -> list[CheckinOut]:
    query = select(Checkin).where(Checkin.user_id == user.id)
    if since:
        query = query.where(Checkin.created_at >= since)
    if until:
        query = query.where(Checkin.created_at <= until)
    rows = await session.scalars(query.order_by(Checkin.created_at.desc()).limit(500))
    key = settings.field_encryption_key.get_secret_value()
    return [_out(row, key) for row in rows]
