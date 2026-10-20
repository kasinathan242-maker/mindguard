"""Deterministic questionnaire scoring. No models, no weighting: the published rules only."""

from collections.abc import Sequence
from dataclasses import dataclass

from app.assessments.instruments import Instrument, NextStep


class InvalidAnswersError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class Score:
    total: int
    max_score: int
    band: str
    next_step: NextStep
    safety_item_positive: bool


def score(instrument: Instrument, answers: Sequence[int]) -> Score:
    if len(answers) != len(instrument.items):
        raise InvalidAnswersError(
            f"{instrument.type} needs exactly {len(instrument.items)} answers, got {len(answers)}"
        )
    # bool is an int subclass; a JSON `true` must not count as a score of 1.
    if any(isinstance(a, bool) or not isinstance(a, int) or not 0 <= a <= 3 for a in answers):
        raise InvalidAnswersError("every answer must be an integer from 0 to 3")

    total = sum(answers)
    band = instrument.band_for(total)
    safety_positive = instrument.safety_item is not None and answers[instrument.safety_item] > 0
    next_step: NextStep = "consult_professional" if safety_positive else band.next_step
    return Score(
        total=total,
        max_score=instrument.max_score,
        band=band.key,
        next_step=next_step,
        safety_item_positive=safety_positive,
    )
