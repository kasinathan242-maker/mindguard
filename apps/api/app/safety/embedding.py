"""Layer 2 (default): multilingual sentence embeddings with a small trained head.

The encoder is `intfloat/multilingual-e5-small` (MIT licence, pinned revision), which covers
English and Tamil and generalises to paraphrases that no pattern list anticipates ("death sounds
like a relief"). A three-way logistic head trained in `ml/safety_eval/train_embedding_head.py`
turns the embedding into none / elevated / urgent scores.

The encoder is loaded once per process; a short message takes roughly 15 ms on a laptop CPU.
"""

import json
import threading
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import torch
from transformers import AutoModel, AutoTokenizer

from app.safety.classifier import LABELS, ClassifierScores
from app.safety.rules import Level

HEAD_FILE = Path(__file__).with_name("embedding_head.json")
MAX_TOKENS = 128


class SentenceEncoder:
    """Mean-pooled, L2-normalised sentence embeddings (the E5 recipe, with its "query: " prefix)."""

    def __init__(self, model_name: str, revision: str) -> None:
        self.model_name = model_name
        self.revision = revision
        self._tokenizer: Any = AutoTokenizer.from_pretrained(model_name, revision=revision)
        self._model: Any = AutoModel.from_pretrained(model_name, revision=revision).eval()
        self._lock = threading.Lock()

    @torch.inference_mode()
    def encode(self, texts: list[str]) -> torch.Tensor:
        batch = self._tokenizer(
            [f"query: {text}" for text in texts],
            padding=True,
            truncation=True,
            max_length=MAX_TOKENS,
            return_tensors="pt",
        )
        with self._lock:  # tokenizers and torch modules are not guaranteed thread-safe
            hidden = self._model(**batch).last_hidden_state
        mask = batch["attention_mask"].unsqueeze(-1).to(hidden.dtype)
        pooled = (hidden * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1e-9)
        return torch.nn.functional.normalize(pooled, dim=1)


@lru_cache
def load_encoder(model_name: str, revision: str) -> SentenceEncoder:
    return SentenceEncoder(model_name, revision)


@dataclass(frozen=True, slots=True)
class EmbeddingClassifier:
    version: str
    encoder: SentenceEncoder
    mean: torch.Tensor  # (dim,) feature standardisation fitted on the training set
    scale: torch.Tensor  # (dim,)
    weight: torch.Tensor  # (3, dim)
    bias: torch.Tensor  # (3,)
    urgent_threshold: float
    flag_threshold: float

    def scores(self, text: str) -> ClassifierScores:
        features = (self.encoder.encode([text])[0] - self.mean) / self.scale
        probs = torch.softmax(self.weight @ features + self.bias, dim=0).tolist()
        return ClassifierScores(*probs)

    def predict(self, text: str) -> tuple[Level, ClassifierScores]:
        scores = self.scores(text)
        return scores.level(self.urgent_threshold, self.flag_threshold), scores


@lru_cache
def load_embedding_classifier(path: Path = HEAD_FILE) -> EmbeddingClassifier | None:
    """The trained head plus its encoder, or None when no head has been exported."""
    if not path.exists():
        return None
    raw = json.loads(path.read_text(encoding="utf-8"))
    if tuple(raw["labels"]) != LABELS:
        raise ValueError("embedding head labels do not match; retrain the head")
    return EmbeddingClassifier(
        version=raw["version"],
        encoder=load_encoder(raw["model"], raw["revision"]),
        mean=torch.tensor(raw["mean"], dtype=torch.float32),
        scale=torch.tensor(raw["scale"], dtype=torch.float32),
        weight=torch.tensor(raw["weight"], dtype=torch.float32),
        bias=torch.tensor(raw["bias"], dtype=torch.float32),
        urgent_threshold=raw["thresholds"]["urgent"],
        flag_threshold=raw["thresholds"]["flag"],
    )
