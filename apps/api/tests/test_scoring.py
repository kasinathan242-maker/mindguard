import pytest

from app.assessments.instruments import GAD7, PHQ9, Instrument
from app.assessments.scoring import InvalidAnswersError, score


def answers_totalling(
    instrument: Instrument, total: int, *, spare_safety_item: bool = True
) -> list[int]:
    """Fill items with 3s then the remainder, leaving the safety item at 0 when asked to."""
    answers = [0] * len(instrument.items)
    order = [
        i for i in range(len(answers)) if not (spare_safety_item and i == instrument.safety_item)
    ]
    remaining = total
    for i in order:
        answers[i] = min(3, remaining)
        remaining -= answers[i]
    assert remaining == 0, "total not reachable without the safety item"
    return answers


PHQ9_BOUNDARIES = [
    (0, "minimal"),
    (4, "minimal"),
    (5, "mild"),
    (9, "mild"),
    (10, "moderate"),
    (14, "moderate"),
    (15, "moderately_severe"),
    (19, "moderately_severe"),
    (20, "severe"),
    (24, "severe"),
]

GAD7_BOUNDARIES = [
    (0, "minimal"),
    (4, "minimal"),
    (5, "mild"),
    (9, "mild"),
    (10, "moderate"),
    (14, "moderate"),
    (15, "severe"),
    (21, "severe"),
]


@pytest.mark.parametrize(("total", "band"), PHQ9_BOUNDARIES)
def test_phq9_band_boundaries(total: int, band: str) -> None:
    result = score(PHQ9, answers_totalling(PHQ9, total))
    assert result.total == total
    assert result.band == band
    assert result.max_score == 27
    assert result.safety_item_positive is False


def test_phq9_maximum_score_is_severe() -> None:
    result = score(PHQ9, [3] * 9)
    assert (result.total, result.band) == (27, "severe")


@pytest.mark.parametrize(("total", "band"), GAD7_BOUNDARIES)
def test_gad7_band_boundaries(total: int, band: str) -> None:
    result = score(GAD7, answers_totalling(GAD7, total))
    assert result.total == total
    assert result.band == band
    assert result.max_score == 21
    assert result.safety_item_positive is False


@pytest.mark.parametrize(
    ("instrument", "total", "step"),
    [
        (PHQ9, 0, "self_care"),
        (PHQ9, 9, "self_care"),
        (PHQ9, 10, "talk_to_someone"),
        (PHQ9, 15, "consult_professional"),
        (GAD7, 4, "self_care"),
        (GAD7, 10, "talk_to_someone"),
        (GAD7, 15, "consult_professional"),
    ],
)
def test_next_step_follows_the_band(instrument: Instrument, total: int, step: str) -> None:
    assert score(instrument, answers_totalling(instrument, total)).next_step == step


@pytest.mark.parametrize("item9", [1, 2, 3])
def test_phq9_item9_triggers_safety_regardless_of_total(item9: int) -> None:
    answers = [0] * 8 + [item9]

    result = score(PHQ9, answers)

    assert result.band == "minimal"
    assert result.safety_item_positive is True
    assert result.next_step == "consult_professional"


def test_gad7_has_no_safety_item() -> None:
    assert score(GAD7, [3] * 7).safety_item_positive is False


@pytest.mark.parametrize(
    ("instrument", "answers"),
    [
        (PHQ9, [0] * 8),
        (PHQ9, [0] * 10),
        (PHQ9, []),
        (GAD7, [0] * 9),
        (GAD7, [0] * 6),
    ],
)
def test_wrong_answer_counts_are_rejected(instrument: Instrument, answers: list[int]) -> None:
    with pytest.raises(InvalidAnswersError, match="exactly"):
        score(instrument, answers)


@pytest.mark.parametrize("bad", [-1, 4, 10, True, 1.0])
def test_out_of_range_or_non_integer_answers_are_rejected(bad: object) -> None:
    answers: list[object] = [0] * 9
    answers[3] = bad
    with pytest.raises(InvalidAnswersError, match="0 to 3"):
        score(PHQ9, answers)  # type: ignore[arg-type]
