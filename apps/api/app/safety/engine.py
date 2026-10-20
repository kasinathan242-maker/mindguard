"""Safety engine: runs on every user message, journal entry and check-in note before any LLM call.

Rules and classifier are combined with OR (the higher level wins), favouring recall: missing a
person in crisis is far worse than showing support resources to someone who did not need them.

Classifier choice (`SAFETY_CLASSIFIER`):
- `embedding` (default): multilingual sentence encoder plus trained head. Generalises to new
  phrasings; needs the encoder weights (downloaded once, baked into the Docker image).
- `hashed`: the dependency-free n-gram model. Used by unit tests and as a fallback.
- `none`: rules only.
"""

import logging
from dataclasses import dataclass
from typing import Literal, Protocol

from app.safety.classifier import ClassifierScores, load_classifier
from app.safety.rules import Level, evaluate_rules, load_rules, max_level

logger = logging.getLogger(__name__)

Detector = Literal["rules", "classifier", "both"]
ClassifierKind = Literal["embedding", "hashed", "none"]


class TextClassifier(Protocol):
    @property
    def version(self) -> str: ...

    def predict(self, text: str) -> tuple[Level, ClassifierScores]: ...


@dataclass(frozen=True, slots=True)
class SafetyAssessment:
    level: Level
    detector: Detector | None
    rule_ids: tuple[str, ...]
    rules_level: Level
    classifier_level: Level
    classifier_scores: ClassifierScores | None
    rules_version: int
    classifier_version: str | None

    @property
    def is_urgent(self) -> bool:
        return self.level == "urgent"


def load_text_classifier(kind: ClassifierKind) -> TextClassifier | None:
    if kind == "none":
        return None
    if kind == "hashed":
        return load_classifier()
    try:
        from app.safety.embedding import load_embedding_classifier  # imports torch lazily

        embedding = load_embedding_classifier()
    except (OSError, ImportError, ValueError):
        # The safety check must keep working even when the encoder weights are missing.
        logger.warning("embedding safety classifier unavailable; using the hashed model")
        embedding = None
    return embedding or load_classifier()


_active: TextClassifier | None = None
_configured = False


def configure(kind: ClassifierKind) -> None:
    """Select and load the classifier once at startup, so the first message is not slow."""
    global _active, _configured
    _active = load_text_classifier(kind)
    _configured = True


def _classifier() -> TextClassifier | None:
    if not _configured:
        configure("hashed")
    return _active


def _detector(level: Level, rules_level: Level, classifier_level: Level) -> Detector | None:
    if level == "none":
        return None
    by_rules = rules_level == level
    by_classifier = classifier_level == level
    if by_rules and by_classifier:
        return "both"
    return "rules" if by_rules else "classifier"


def assess(text: str, classifier: TextClassifier | None = None) -> SafetyAssessment:
    rules = evaluate_rules(text)
    model = classifier if classifier is not None else _classifier()
    classifier_level: Level = "none"
    scores: ClassifierScores | None = None
    if model is not None:
        classifier_level, scores = model.predict(text)

    level = max_level(rules.level, classifier_level)
    return SafetyAssessment(
        level=level,
        detector=_detector(level, rules.level, classifier_level),
        rule_ids=tuple(rules.rule_ids),
        rules_level=rules.level,
        classifier_level=classifier_level,
        classifier_scores=scores,
        rules_version=load_rules().version,
        classifier_version=model.version if model is not None else None,
    )
