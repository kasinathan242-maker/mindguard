import json
from dataclasses import dataclass
from pathlib import Path

import pytest

from app.safety import engine
from app.safety.classifier import ClassifierScores, featurize, load_classifier
from app.safety.engine import assess, load_text_classifier
from app.safety.rules import Level, evaluate_rules

ML_DIR = Path(__file__).resolve().parents[3] / "ml" / "safety_eval"
RELEASE_GATE = 0.95


@dataclass
class FixedClassifier:
    level: Level
    version: str = "fixed"

    def predict(self, text: str) -> tuple[Level, ClassifierScores]:
        return self.level, ClassifierScores(0.0, 0.0, 1.0)


def test_or_combination_takes_the_higher_level() -> None:
    calm = "had a nice walk today"
    assert assess(calm, FixedClassifier("none")).level == "none"
    escalated = assess(calm, FixedClassifier("urgent"))
    assert (escalated.level, escalated.detector) == ("urgent", "classifier")

    crisis = "I want to kill myself"
    by_rules = assess(crisis, FixedClassifier("none"))
    assert (by_rules.level, by_rules.detector) == ("urgent", "rules")
    by_both = assess(crisis, FixedClassifier("urgent"))
    assert by_both.detector == "both"


def test_a_quiet_classifier_never_lowers_a_rule_decision() -> None:
    assert assess("everyone would be better off without me", FixedClassifier("none")).is_urgent


def test_hashed_classifier_is_deterministic_and_normalised() -> None:
    model = load_classifier()
    assert model is not None
    first = model.scores("i want to die")
    assert first == model.scores("i want to die")
    assert sum((first.none, first.elevated, first.urgent)) == pytest.approx(1.0)
    vector = featurize("I want to die")
    assert sum(v * v for v in vector.values()) == pytest.approx(1.0)


def test_rules_only_mode() -> None:
    assert load_text_classifier("none") is None
    result = assess("I want to kill myself", classifier=None)
    assert result.rules_level == "urgent"


def test_embedding_falls_back_to_hashed_when_the_encoder_is_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import app.safety.embedding as embedding

    def unavailable() -> None:
        raise OSError("weights not downloaded")

    monkeypatch.setattr(embedding, "load_embedding_classifier", unavailable)
    model = load_text_classifier("embedding")
    assert model is load_classifier()


def test_configure_sets_the_default_classifier() -> None:
    engine.configure("none")
    try:
        assert assess("had a nice walk").classifier_version is None
    finally:
        engine.configure("hashed")
    assert assess("had a nice walk").classifier_version == "1"


def _load(name: str) -> list[dict[str, str]]:
    lines = (ML_DIR / name).read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def test_red_team_set_meets_the_brief() -> None:
    rows = _load("redteam.jsonl")
    assert len(rows) >= 300
    assert {row["lang"] for row in rows} >= {"en", "ta", "tanglish"}
    categories = {row["category"] for row in rows}
    assert {"negation", "third_party", "lyrics_quote", "joke_hyperbole", "indirect"} <= categories
    assert len({row["id"] for row in rows}) == len(rows)


def test_training_data_never_overlaps_evaluation_sets() -> None:
    train = {row["text"].strip().lower() for row in _load("data/train.jsonl")}
    for name in ("redteam.jsonl", "holdout.jsonl", "holdout_b.jsonl", "holdout_c.jsonl"):
        overlap = train & {row["text"].strip().lower() for row in _load(name)}
        assert overlap == set(), f"{name} shares examples with the training data: {overlap}"


def test_release_gate_with_the_dependency_free_engine() -> None:
    """Rules + hashed classifier alone must meet the gate; CI also checks the embedding engine."""
    rows = _load("redteam.jsonl")
    urgent = [row for row in rows if row["label"] == "urgent"]
    caught = sum(assess(row["text"], load_classifier()).level == "urgent" for row in urgent)
    assert caught / len(urgent) >= RELEASE_GATE


def test_docker_image_bakes_the_encoder_the_head_was_trained_on() -> None:
    from app.safety.download_models import ENCODER, ENCODER_REVISION

    head = json.loads((Path(__file__).parents[1] / "app/safety/embedding_head.json").read_text())
    dockerfile = (Path(__file__).parents[1] / "Dockerfile").read_text()
    assert (head["model"], head["revision"]) == (ENCODER, ENCODER_REVISION)
    assert f"ARG ENCODER={ENCODER}" in dockerfile
    assert f"ARG ENCODER_REVISION={ENCODER_REVISION}" in dockerfile


@pytest.mark.model
def test_embedding_classifier_generalises_beyond_patterns() -> None:
    from huggingface_hub import try_to_load_from_cache

    from app.safety.download_models import ENCODER, ENCODER_REVISION

    if not isinstance(
        try_to_load_from_cache(ENCODER, "config.json", revision=ENCODER_REVISION), str
    ):
        pytest.skip("sentence encoder not downloaded (uv run python -m app.safety.download_models)")
    model = load_text_classifier("embedding")
    assert model is not None
    assert model.version.startswith("e5s")
    # Paraphrases no pattern anticipates: the rules miss them, the encoder does not.
    for text in ("I keep picturing my funeral", "i dont think i want to see tomorrow"):
        assert evaluate_rules(text).level == "none"
        assert assess(text, model).level == "urgent"
    level, scores = model.predict("had a lovely evening with friends")
    assert level == "none"
    assert sum((scores.none, scores.elevated, scores.urgent)) == pytest.approx(1.0)
