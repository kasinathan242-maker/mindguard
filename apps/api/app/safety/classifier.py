"""Layer 2 of the safety engine: a small linear text classifier.

A multinomial logistic regression over hashed word and character n-grams. It is trained with
PyTorch in `ml/safety_eval/train_classifier.py` and exported to `classifier_weights.json`;
inference here is plain Python, so the safety check needs no ML runtime, starts instantly and
takes well under a millisecond per message.

The featuriser below is the single source of truth: the training script imports it, so training
and serving can never featurise text differently.
"""

import json
import math
import re
import zlib
from collections import Counter
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from app.safety.normalize import normalize
from app.safety.rules import Level

WEIGHTS_FILE = Path(__file__).with_name("classifier_weights.json")
FEATURE_DIM = 1 << 15
LABELS: tuple[Level, ...] = ("none", "elevated", "urgent")

_TOKEN = re.compile(r"[\w஀-௿]+")


def _bucket(feature: str) -> int:
    return zlib.crc32(feature.encode("utf-8")) & (FEATURE_DIM - 1)


def featurize(text: str) -> dict[int, float]:
    """Sparse, L2-normalised log-count vector of word 1-2 grams and in-word char 3-5 grams."""
    words = _TOKEN.findall(normalize(text))
    counts: Counter[int] = Counter()
    for i, word in enumerate(words):
        counts[_bucket(f"w:{word}")] += 1
        if i + 1 < len(words):
            counts[_bucket(f"b:{word}_{words[i + 1]}")] += 1
        padded = f" {word} "
        for n in (3, 4, 5):
            for start in range(max(len(padded) - n + 1, 0)):
                counts[_bucket(f"c:{padded[start : start + n]}")] += 1
    weighted = {index: 1.0 + math.log(count) for index, count in counts.items()}
    norm = math.sqrt(sum(v * v for v in weighted.values())) or 1.0
    return {index: value / norm for index, value in weighted.items()}


@dataclass(frozen=True, slots=True)
class ClassifierScores:
    none: float
    elevated: float
    urgent: float

    def level(self, urgent_threshold: float, flag_threshold: float) -> Level:
        if self.urgent >= urgent_threshold:
            return "urgent"
        if self.urgent + self.elevated >= flag_threshold:
            return "elevated"
        return "none"


@dataclass(frozen=True, slots=True)
class SafetyClassifier:
    version: str
    bias: tuple[float, float, float]
    weights: dict[int, tuple[float, float, float]]
    urgent_threshold: float
    flag_threshold: float

    def scores(self, text: str) -> ClassifierScores:
        logits = list(self.bias)
        for index, value in featurize(text).items():
            row = self.weights.get(index)
            if row is not None:
                for k in range(3):
                    logits[k] += row[k] * value
        peak = max(logits)
        exps = [math.exp(v - peak) for v in logits]
        total = sum(exps)
        return ClassifierScores(*(e / total for e in exps))

    def predict(self, text: str) -> tuple[Level, ClassifierScores]:
        scores = self.scores(text)
        return scores.level(self.urgent_threshold, self.flag_threshold), scores


@lru_cache
def load_classifier(path: Path = WEIGHTS_FILE) -> SafetyClassifier | None:
    """The trained classifier, or None when no weights have been exported yet."""
    if not path.exists():
        return None
    raw = json.loads(path.read_text(encoding="utf-8"))
    if raw["feature_dim"] != FEATURE_DIM or tuple(raw["labels"]) != LABELS:
        raise ValueError("classifier weights do not match the featuriser; retrain the model")
    return SafetyClassifier(
        version=raw["version"],
        bias=tuple(raw["bias"]),
        weights={int(k): tuple(v) for k, v in raw["weights"].items()},
        urgent_threshold=raw["thresholds"]["urgent"],
        flag_threshold=raw["thresholds"]["flag"],
    )
