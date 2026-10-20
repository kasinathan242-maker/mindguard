"""Train the embedding classifier's head and export it for the API.

Run from apps/api, whose environment has PyTorch and transformers:

    cd apps/api
    uv run python ../../ml/safety_eval/train_embedding_head.py

Trains only on `data/train.jsonl`. The encoder is frozen; only a 3-way logistic head is learned.
Thresholds come from 5-fold cross-validation on the training set: the lowest threshold (highest
recall) whose out-of-fold false-positive rate stays within the cap. Without the cap the head
would flag nearly everything, which would replace conversations with crisis cards.
"""

import json
import random
import sys
from pathlib import Path

import torch

API_ROOT = Path(__file__).resolve().parents[2] / "apps" / "api"
sys.path.insert(0, str(API_ROOT))

from app.safety.classifier import LABELS  # noqa: E402
from app.safety.embedding import HEAD_FILE, load_encoder  # noqa: E402

TRAIN_FILE = Path(__file__).with_name("data") / "train.jsonl"
MODEL = "intfloat/multilingual-e5-small"
REVISION = "614241f622f53c4eeff9890bdc4f31cfecc418b3"
SEED = 20261020
EPOCHS = 600
LR = 0.05
L2 = 1e-3
FOLDS = 5
MAX_URGENT_FPR = 0.10
MAX_FLAG_FPR = 0.15
VERSION = "e5s-1"


def load() -> tuple[list[str], torch.Tensor]:
    texts, labels = [], []
    for line in TRAIN_FILE.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            texts.append(row["text"])
            labels.append(LABELS.index(row["label"]))
    return texts, torch.tensor(labels)


def train(x: torch.Tensor, y: torch.Tensor) -> torch.nn.Linear:
    torch.manual_seed(SEED)
    head = torch.nn.Linear(x.shape[1], len(LABELS))
    counts = torch.bincount(y, minlength=len(LABELS)).float()
    loss_fn = torch.nn.CrossEntropyLoss(weight=counts.sum() / (len(LABELS) * counts.clamp(min=1)))
    optimiser = torch.optim.Adam(head.parameters(), lr=LR, weight_decay=L2)
    for _ in range(EPOCHS):
        optimiser.zero_grad()
        loss_fn(head(x), y).backward()
        optimiser.step()
    return head


def best_threshold(scores: torch.Tensor, positive: torch.Tensor, max_fpr: float) -> float:
    best = 0.95
    for candidate in [t / 100 for t in range(95, 4, -1)]:
        if (scores[~positive] >= candidate).float().mean().item() > max_fpr:
            break
        best = candidate
    return best


def cross_validated_probs(x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
    order = list(range(len(y)))
    random.Random(SEED).shuffle(order)
    probs = torch.zeros(len(y), len(LABELS))
    for fold in range(FOLDS):
        held = order[fold::FOLDS]
        held_set = set(held)
        kept = [i for i in order if i not in held_set]
        head = train(x[kept], y[kept])
        with torch.no_grad():
            probs[held] = torch.softmax(head(x[held]), dim=1)
    return probs


def main() -> None:
    texts, y = load()
    raw = load_encoder(MODEL, REVISION).encode(texts).clone()
    # Standardise: E5 embeddings share a large common direction that a linear head cannot use.
    mean, scale = raw.mean(dim=0), raw.std(dim=0).clamp(min=1e-6)
    x = (raw - mean) / scale
    probs = cross_validated_probs(x, y)
    urgent, elevated, none = (LABELS.index(k) for k in ("urgent", "elevated", "none"))
    urgent_threshold = best_threshold(probs[:, urgent], y == urgent, MAX_URGENT_FPR)
    flag_threshold = best_threshold(probs[:, urgent] + probs[:, elevated], y != none, MAX_FLAG_FPR)
    cv_recall = (probs[y == urgent, urgent] >= urgent_threshold).float().mean().item()
    print(  # noqa: T201
        f"thresholds urgent={urgent_threshold} flag={flag_threshold}; "
        f"cross-validated urgent recall {cv_recall:.3f}"
    )

    head = train(x, y)
    HEAD_FILE.write_text(
        json.dumps(
            {
                "version": VERSION,
                "model": MODEL,
                "revision": REVISION,
                "labels": list(LABELS),
                "mean": [round(v, 6) for v in mean.tolist()],
                "scale": [round(v, 6) for v in scale.tolist()],
                "weight": [[round(v, 6) for v in row] for row in head.weight.detach().tolist()],
                "bias": [round(v, 6) for v in head.bias.detach().tolist()],
                "thresholds": {"urgent": urgent_threshold, "flag": flag_threshold},
                "training": {
                    "file": "ml/safety_eval/data/train.jsonl",
                    "examples": len(texts),
                    "seed": SEED,
                    "epochs": EPOCHS,
                    "learning_rate": LR,
                    "l2": L2,
                    "cross_validated_urgent_recall": round(cv_recall, 3),
                    "threshold_rule": f"lowest threshold with {FOLDS}-fold CV false-positive "
                    f"rate <= {MAX_URGENT_FPR} (urgent) / {MAX_FLAG_FPR} (flag)",
                },
            },
            indent=1,
        ),
        encoding="utf-8",
    )
    print(f"exported head to {HEAD_FILE}")  # noqa: T201


if __name__ == "__main__":
    main()
