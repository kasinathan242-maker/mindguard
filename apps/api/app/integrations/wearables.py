"""Wearable data import (v1): daily aggregates from a CSV file the person uploads.

Google Fit is deprecated and Health Connect / HealthKit are on-device only, so a web backend
cannot pull them. People export daily totals and upload them here. Expected columns:

    day,sleep_minutes,steps,resting_hr
    2026-10-01,420,6500,64

Any of the three metric columns may be empty. Only daily aggregates are accepted.
"""

import csv
import io
import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy import Date, ForeignKey, String, UniqueConstraint, delete, select
from sqlalchemy.orm import Mapped, mapped_column

from app.auth.models import User
from app.consent.deps import require_consent
from app.core.deps import SessionDep
from app.db.base import Base

MAX_BYTES = 512 * 1024
MAX_ROWS = 400
COLUMNS = ("day", "sleep_minutes", "steps", "resting_hr")
RANGES: dict[str, tuple[int, int]] = {
    "sleep_minutes": (0, 1440),
    "steps": (0, 100_000),
    "resting_hr": (25, 220),
}


class WearableSample(Base):
    __tablename__ = "wearable_samples"
    __table_args__ = (UniqueConstraint("user_id", "metric", "day"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    metric: Mapped[str] = mapped_column(String(16))
    value: Mapped[float]
    day: Mapped[date] = mapped_column(Date)
    source: Mapped[str] = mapped_column(String(16), default="csv")


class InvalidFileError(ValueError):
    pass


def parse_csv(raw: bytes) -> list[tuple[date, str, float]]:
    """Validate the whole file before anything is stored; reject it on the first bad row."""
    if len(raw) > MAX_BYTES:
        raise InvalidFileError(f"file is larger than {MAX_BYTES // 1024} KB")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise InvalidFileError("file is not UTF-8 text") from exc
    reader = csv.DictReader(io.StringIO(text))
    if tuple(reader.fieldnames or ()) != COLUMNS:
        raise InvalidFileError(f"header must be exactly: {','.join(COLUMNS)}")
    rows: list[tuple[date, str, float]] = []
    seen: set[date] = set()
    for line, record in enumerate(reader, start=2):
        if line - 1 > MAX_ROWS:
            raise InvalidFileError(f"at most {MAX_ROWS} days per file")
        try:
            day = date.fromisoformat(record["day"])
        except (TypeError, ValueError) as exc:
            raise InvalidFileError(f"line {line}: day must be YYYY-MM-DD") from exc
        if day in seen:
            raise InvalidFileError(f"line {line}: {day} appears twice")
        if day > date.today():
            raise InvalidFileError(f"line {line}: {day} is in the future")
        seen.add(day)
        for metric, (low, high) in RANGES.items():
            cell = (record.get(metric) or "").strip()
            if not cell:
                continue
            try:
                value = float(cell)
            except ValueError as exc:
                raise InvalidFileError(f"line {line}: {metric} must be a number") from exc
            if not low <= value <= high:
                raise InvalidFileError(f"line {line}: {metric} must be between {low} and {high}")
            rows.append((day, metric, value))
    if not rows:
        raise InvalidFileError("no data rows found")
    return rows


router = APIRouter(prefix="/integrations/wearables", tags=["integrations"])
WearablesUser = Annotated[User, Depends(require_consent("wearables"))]


class ImportResult(BaseModel):
    days: int
    values: int


class DailyValue(BaseModel):
    day: date
    metric: str
    value: float


@router.post("/import")
async def import_csv(file: UploadFile, user: WearablesUser, session: SessionDep) -> ImportResult:
    name = (file.filename or "").lower()
    if not name.endswith(".csv") or file.content_type not in {
        "text/csv",
        "application/vnd.ms-excel",
        "text/plain",
        "application/octet-stream",
    }:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "Upload a .csv file")
    try:
        rows = parse_csv(await file.read(MAX_BYTES + 1))
    except InvalidFileError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from None
    days = {day for day, _, _ in rows}
    await session.execute(
        delete(WearableSample).where(
            WearableSample.user_id == user.id, WearableSample.day.in_(days)
        )
    )
    session.add_all(
        WearableSample(user_id=user.id, metric=m, value=v, day=d, source="csv") for d, m, v in rows
    )
    await session.commit()
    return ImportResult(days=len(days), values=len(rows))


@router.get("")
async def list_values(user: WearablesUser, session: SessionDep) -> list[DailyValue]:
    rows = await session.scalars(
        select(WearableSample)
        .where(WearableSample.user_id == user.id)
        .order_by(WearableSample.day.desc())
        .limit(1200)
    )
    return [DailyValue(day=r.day, metric=r.metric, value=r.value) for r in rows]


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def delete_all(user: WearablesUser, session: SessionDep) -> None:
    await session.execute(delete(WearableSample).where(WearableSample.user_id == user.id))
    await session.commit()
