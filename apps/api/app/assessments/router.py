from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select

from app.assessments.instruments import (
    ATTRIBUTION,
    DIFFICULTY_OPTIONS,
    FREQUENCY_OPTIONS,
    INSTRUMENTS,
    InstrumentType,
    get_instrument,
)
from app.assessments.models import Assessment
from app.assessments.schemas import AssessmentIn, AssessmentOut, InstrumentOut, Item, Option
from app.assessments.scoring import InvalidAnswersError, score
from app.auth.models import User
from app.consent.deps import require_consent
from app.core.deps import SessionDep
from app.safety.service import record_safety_event

router = APIRouter(prefix="/assessments", tags=["assessments"])

CoreUser = Annotated[User, Depends(require_consent("core"))]


def _to_out(row: Assessment) -> AssessmentOut:
    instrument = get_instrument(row.type)
    result = score(instrument, row.answers)
    return AssessmentOut(
        id=row.id,
        type=instrument.type,
        total=row.total,
        max_score=instrument.max_score,
        severity_band=row.severity_band,
        next_step=result.next_step,
        safety_item_positive=row.safety_item_positive,
        functional_difficulty=row.functional_difficulty,
        created_at=row.created_at,
    )


@router.get("/history")
async def history(
    user: CoreUser,
    session: SessionDep,
    instrument_type: Annotated[InstrumentType | None, Query(alias="type")] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> list[AssessmentOut]:
    query = select(Assessment).where(Assessment.user_id == user.id)
    if instrument_type is not None:
        query = query.where(Assessment.type == instrument_type)
    rows = await session.scalars(query.order_by(Assessment.created_at.desc()).limit(limit))
    return [_to_out(row) for row in rows]


@router.get("/{instrument_type}/items")
async def items(
    instrument_type: InstrumentType, locale: Literal["en", "ta"] = "en"
) -> InstrumentOut:
    instrument = INSTRUMENTS[instrument_type]
    return InstrumentOut(
        type=instrument.type,
        title=instrument.title,
        stem=instrument.stem,
        items=[Item(index=i, text=text) for i, text in enumerate(instrument.items)],
        options=[Option(value=v, label=label) for v, label in enumerate(FREQUENCY_OPTIONS)],
        difficulty_question=instrument.difficulty_question,
        difficulty_options=[
            Option(value=v, label=label) for v, label in enumerate(DIFFICULTY_OPTIONS)
        ],
        item_locale="en",
        requested_locale=locale,
        translation_available=locale == "en",
        attribution=ATTRIBUTION,
    )


@router.post("/{instrument_type}", status_code=status.HTTP_201_CREATED)
async def submit(
    instrument_type: InstrumentType, body: AssessmentIn, user: CoreUser, session: SessionDep
) -> AssessmentOut:
    instrument = INSTRUMENTS[instrument_type]
    try:
        result = score(instrument, body.answers)
    except InvalidAnswersError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        ) from None

    row = Assessment(
        user_id=user.id,
        type=instrument.type,
        answers=list(body.answers),
        total=result.total,
        severity_band=result.band,
        safety_item_positive=result.safety_item_positive,
        functional_difficulty=body.functional_difficulty,
    )
    session.add(row)
    if result.safety_item_positive:
        record_safety_event(
            session, user.id, source="phq9_item9", level="urgent", detector="questionnaire"
        )
    await session.commit()
    return _to_out(row)
