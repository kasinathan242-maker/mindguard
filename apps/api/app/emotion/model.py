"""Text emotion (experimental): an English GoEmotions classifier mapped to seven broad labels.

Model: `SamLowe/roberta-base-go_emotions` (MIT licence, pinned revision). Its 28 GoEmotions labels
are grouped into Ekman's six emotions plus neutral, the grouping published with GoEmotions.

Outputs are deliberately humble:
- `unsupported` for Tamil script or romanised Tamil (no evaluated Tamil model exists yet),
- `uncertain` when the top group's score is below the confidence threshold,
- otherwise one of anger, disgust, fear, joy, sadness, surprise, neutral.
The label is shown to the person as a dismissible guess, never as a verdict.
"""

import re
import threading
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Literal

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

MODEL = "SamLowe/roberta-base-go_emotions"
REVISION = "d75048347613a25d77de8cf6412eaae9fa7b26be"
CONFIDENCE_THRESHOLD = 0.5

EmotionLabel = Literal["anger", "disgust", "fear", "joy", "sadness", "surprise", "neutral"]
Prediction = EmotionLabel | Literal["uncertain", "unsupported"]

# GoEmotions' published Ekman mapping.
EKMAN: dict[str, EmotionLabel] = {
    **dict.fromkeys(["anger", "annoyance", "disapproval"], "anger"),
    "disgust": "disgust",
    **dict.fromkeys(["fear", "nervousness"], "fear"),
    **dict.fromkeys(
        [
            "joy",
            "amusement",
            "approval",
            "excitement",
            "gratitude",
            "love",
            "optimism",
            "relief",
            "pride",
            "admiration",
            "desire",
            "caring",
        ],
        "joy",
    ),
    **dict.fromkeys(["sadness", "disappointment", "embarrassment", "grief", "remorse"], "sadness"),
    **dict.fromkeys(["surprise", "realization", "confusion", "curiosity"], "surprise"),
    "neutral": "neutral",
}

_TAMIL_SCRIPT = re.compile("[" + chr(0x0B80) + "-" + chr(0x0BFF) + "]")
# Frequent romanised-Tamil function words. Two or more in a short message marks it as Tanglish.
_TANGLISH_WORDS = frozenset(
    [
        "da",
        "di",
        "illa",
        "illai",
        "irukku",
        "iruku",
        "panna",
        "pannu",
        "pannren",
        "romba",
        "enna",
        "epdi",
        "ippo",
        "inniku",
        "naan",
        "nee",
        "enakku",
        "unakku",
        "sollu",
        "solla",
        "venum",
        "vendam",
        "aana",
        "aamaa",
        "paaru",
        "po",
        "vaa",
        "thaan",
        "dhaan",
        "nalla",
        "kashtam",
        "theriyala",
        "mudiyala",
        "pidikala",
    ]
)


def is_tamil_or_tanglish(text: str) -> bool:
    if _TAMIL_SCRIPT.search(text):
        return True
    words = re.findall(r"[a-z]+", text.lower())
    return sum(w in _TANGLISH_WORDS for w in words) >= 2


@dataclass(frozen=True, slots=True)
class EmotionResult:
    label: Prediction
    confidence: float | None


class EmotionModel:
    def __init__(self, model: str = MODEL, revision: str = REVISION) -> None:
        self._tokenizer: Any = AutoTokenizer.from_pretrained(model, revision=revision)
        self._model: Any = AutoModelForSequenceClassification.from_pretrained(
            model, revision=revision
        ).eval()
        self._labels: list[str] = [
            self._model.config.id2label[i] for i in range(self._model.config.num_labels)
        ]
        self._lock = threading.Lock()

    @torch.inference_mode()
    def group_scores(self, texts: list[str]) -> list[dict[EmotionLabel, float]]:
        batch = self._tokenizer(
            texts, padding=True, truncation=True, max_length=128, return_tensors="pt"
        )
        with self._lock:
            probs = torch.sigmoid(self._model(**batch).logits)
        out = []
        for row in probs.tolist():
            groups: dict[EmotionLabel, float] = {}
            for name, p in zip(self._labels, row, strict=True):
                group = EKMAN[name]
                groups[group] = max(groups.get(group, 0.0), p)
            out.append(groups)
        return out

    def predict(self, text: str) -> EmotionResult:
        if is_tamil_or_tanglish(text):
            return EmotionResult("unsupported", None)
        scores = self.group_scores([text])[0]
        label, confidence = max(scores.items(), key=lambda item: item[1])
        if confidence < CONFIDENCE_THRESHOLD:
            return EmotionResult("uncertain", round(confidence, 3))
        return EmotionResult(label, round(confidence, 3))


@lru_cache
def load_emotion_model() -> EmotionModel:
    return EmotionModel()
