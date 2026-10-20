import uuid
from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field

from app.assessments.instruments import InstrumentType, NextStep


class Option(BaseModel):
    value: int
    label: str


class Item(BaseModel):
    index: int
    text: str


class InstrumentOut(BaseModel):
    type: InstrumentType
    title: str
    stem: str
    items: list[Item]
    options: list[Option]
    difficulty_question: str
    difficulty_options: list[Option]
    item_locale: Literal["en"]
    requested_locale: Literal["en", "ta"]
    translation_available: bool
    attribution: str


class AssessmentIn(BaseModel):
    # Element range is validated by the scoring rules, which own the 0-3 constraint.
    answers: Annotated[list[int], Field(min_length=1, max_length=9)]
    functional_difficulty: Annotated[int | None, Field(ge=0, le=3)] = None


class AssessmentOut(BaseModel):
    id: uuid.UUID
    type: InstrumentType
    total: int
    max_score: int
    severity_band: str
    next_step: NextStep
    safety_item_positive: bool
    functional_difficulty: int | None
    created_at: datetime
