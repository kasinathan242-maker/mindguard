"""PHQ-9 and GAD-7 item text and scoring bands.

Item wording is reproduced verbatim from the published English instruments (Spitzer, Williams,
Kroenke and colleagues; "No permission required to reproduce, translate, display or
distribute"). Do not paraphrase, shorten or translate items here: only official, validated
translations may be added, with their source recorded in docs/DECISIONS.md.
"""

from dataclasses import dataclass
from typing import Literal

InstrumentType = Literal["PHQ9", "GAD7"]
NextStep = Literal["self_care", "talk_to_someone", "consult_professional"]

ATTRIBUTION = (
    "Developed by Drs. Robert L. Spitzer, Janet B.W. Williams, Kurt Kroenke and colleagues, "
    "with an educational grant from Pfizer Inc. No permission required to reproduce, "
    "translate, display or distribute."
)

FREQUENCY_OPTIONS: tuple[str, ...] = (
    "Not at all",
    "Several days",
    "More than half the days",
    "Nearly every day",
)

DIFFICULTY_OPTIONS: tuple[str, ...] = (
    "Not difficult at all",
    "Somewhat difficult",
    "Very difficult",
    "Extremely difficult",
)


@dataclass(frozen=True, slots=True)
class Band:
    key: str
    low: int
    high: int
    next_step: NextStep


@dataclass(frozen=True, slots=True)
class Instrument:
    type: InstrumentType
    # Short public name. The full official titles are not shown in the UI because they use
    # clinical labels ("Patient", "Disorder") that the product's microcopy avoids.
    title: str
    stem: str
    items: tuple[str, ...]
    difficulty_question: str
    bands: tuple[Band, ...]
    # 0-based index of the item that opens the safety flow when answered above 0.
    safety_item: int | None = None

    @property
    def max_score(self) -> int:
        return 3 * len(self.items)

    def band_for(self, total: int) -> Band:
        for band in self.bands:
            if band.low <= total <= band.high:
                return band
        raise ValueError(f"{self.type} total {total} is outside 0..{self.max_score}")


PHQ9 = Instrument(
    type="PHQ9",
    title="PHQ-9",
    stem=(
        "Over the last 2 weeks, how often have you been bothered by any of the following problems?"
    ),
    items=(
        "Little interest or pleasure in doing things",
        "Feeling down, depressed, or hopeless",
        "Trouble falling or staying asleep, or sleeping too much",
        "Feeling tired or having little energy",
        "Poor appetite or overeating",
        "Feeling bad about yourself — or that you are a failure or have let yourself or "
        "your family down",
        "Trouble concentrating on things, such as reading the newspaper or watching television",
        "Moving or speaking so slowly that other people could have noticed? Or the opposite "
        "— being so fidgety or restless that you have been moving around a lot more than "
        "usual",
        "Thoughts that you would be better off dead or of hurting yourself in some way",
    ),
    difficulty_question=(
        "If you checked off any problems, how difficult have these problems made it for you to "
        "do your work, take care of things at home, or get along with other people?"
    ),
    bands=(
        Band("minimal", 0, 4, "self_care"),
        Band("mild", 5, 9, "self_care"),
        Band("moderate", 10, 14, "talk_to_someone"),
        Band("moderately_severe", 15, 19, "consult_professional"),
        Band("severe", 20, 27, "consult_professional"),
    ),
    safety_item=8,
)

GAD7 = Instrument(
    type="GAD7",
    title="GAD-7",
    stem="Over the last 2 weeks, how often have you been bothered by the following problems?",
    items=(
        "Feeling nervous, anxious, or on edge",
        "Not being able to stop or control worrying",
        "Worrying too much about different things",
        "Trouble relaxing",
        "Being so restless that it is hard to sit still",
        "Becoming easily annoyed or irritable",
        "Feeling afraid, as if something awful might happen",
    ),
    difficulty_question=(
        "If you checked off any problems, how difficult have these problems made it for you to "
        "do your work, take care of things at home, or get along with other people?"
    ),
    bands=(
        Band("minimal", 0, 4, "self_care"),
        Band("mild", 5, 9, "self_care"),
        Band("moderate", 10, 14, "talk_to_someone"),
        Band("severe", 15, 21, "consult_professional"),
    ),
)

INSTRUMENTS: dict[InstrumentType, Instrument] = {"PHQ9": PHQ9, "GAD7": GAD7}


def get_instrument(instrument_type: str) -> Instrument:
    for instrument in INSTRUMENTS.values():
        if instrument.type == instrument_type:
            return instrument
    raise KeyError(instrument_type)
