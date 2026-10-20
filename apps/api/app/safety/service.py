import uuid
from typing import Literal

from sqlalchemy.ext.asyncio import AsyncSession

from app.safety.models import SafetyEvent
from app.safety.resources import resource_ids

SafetySource = Literal["chat", "phq9_item9", "journal", "checkin"]
SafetyLevel = Literal["elevated", "urgent"]
Detector = Literal["rules", "classifier", "both", "questionnaire"]


def record_safety_event(
    session: AsyncSession,
    user_id: uuid.UUID,
    *,
    source: SafetySource,
    level: SafetyLevel,
    detector: Detector,
) -> None:
    """Stage a content-free record that the crisis resources were shown."""
    session.add(
        SafetyEvent(
            user_id=user_id,
            source=source,
            level=level,
            detector=detector,
            resources_shown=resource_ids(),
        )
    )
