"""Train the safety classifier (layer 2) and export it for the API.

    cd ml
    uv run python safety_eval/train_classifier.py

Trains only on `data/train.jsonl`; the red-team set is never used for training or for choosing
thresholds. The featuriser is imported from the API so serving and training cannot drift.

Model: multinomial logistic regression over hashed n-gram features, class-balanced loss and L2
regularisation. Thresholds are chosen by 5-fold cross-validation on the training set: each is
the value with the best out-of-fold recall whose out-of-fold false-positive rate stays within
MAX_FPR. Capping false positives matters: a threshold picked for recall alone flags nearly every
message, which would send most people to the crisis card instead of a conversation.
"""

import json
import random
import sys
from pathlib import Path

import torch

API_ROOT = Path(__file__).resolve().parents[2] / "apps" / "api"
sys.path.insert(0, str(API_ROOT))

from app.safety.classifier import FEATURE_DIM, LABELS, WEIGHTS_FILE, featurize  # noqa: E402

TRAIN_FILE = Path(__file__).with_name("data") / "train.jsonl"
SEED = 20261020
EPOCHS = 400
LR = 0.05
L2 = 2e-4
MAX_URGENT_FPR = 0.10
MAX_FLAG_FPR = 0.15
FOLDS = 5
VERSION = "1"


def load() -> tuple[list[str], list[int]]:
    texts, labels = [], []
    for line in TRAIN_FILE.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            texts.append(row["text"])
            labels.append(LABELS.index(row["label"]))
    return texts, labels


def to_matrix(texts: list[str]) -> torch.Tensor:
    matrix = torch.zeros(len(texts), FEATURE_DIM)
    for i, text in enumerate(texts):
        for index, value in featurize(text).items():
            matrix[i, index] = value
    return matrix


def train(x: torch.Tensor, y: torch.Tensor) -> torch.nn.Linear:
    torch.manual_seed(SEED)
    model = torch.nn.Linear(FEATURE_DIM, len(LABELS))
    torch.nn.init.zeros_(model.weight)
    torch.nn.init.zeros_(model.bias)
    counts = torch.bincount(y, minlength=len(LABELS)).float()
    class_weight = counts.sum() / (len(LABELS) * counts.clamp(min=1))
    loss_fn = torch.nn.CrossEntropyLoss(weight=class_weight)
    optimiser = torch.optim.Adam(model.parameters(), lr=LR, weight_decay=L2)
    for _ in range(EPOCHS):
        optimiser.zero_grad()
        loss = loss_fn(model(x), y)
        loss.backward()
        optimiser.step()
    return model


def _best_threshold(scores: torch.Tensor, positive: torch.Tensor, max_fpr: float) -> float:
    """Lowest threshold (so highest recall) whose false-positive rate is within max_fpr."""
    best = 0.95
    for candidate in [t / 100 for t in range(95, 4, -1)]:
        predicted = scores >= candidate
        fpr = predicted[~positive].float().mean().item()
        if fpr > max_fpr:
            break
        best = candidate
    return best


def choose_thresholds(x: torch.Tensor, y: torch.Tensor) -> tuple[float, float]:
    order = list(range(len(y)))
    random.Random(SEED).shuffle(order)
    probs = torch.zeros(len(y), len(LABELS))
    for fold in range(FOLDS):
        held = order[fold::FOLDS]
        kept = [i for i in order if i not in set(held)]
        model = train(x[kept], y[kept])
        with torch.no_grad():
            probs[held] = torch.softmax(model(x[held]), dim=1)

    urgent = LABELS.index("urgent")
    elevated = LABELS.index("elevated")
    urgent_threshold = _best_threshold(probs[:, urgent], y == urgent, MAX_URGENT_FPR)
    flag_threshold = _best_threshold(
        probs[:, urgent] + probs[:, elevated], y != LABELS.index("none"), MAX_FLAG_FPR
    )
    return urgent_threshold, flag_threshold


def export(model: torch.nn.Linear, urgent_threshold: float, flag_threshold: float) -> None:
    weight = model.weight.detach().T  # (FEATURE_DIM, 3)
    keep = weight.abs().max(dim=1).values > 1e-4
    rows = {
        str(int(index)): [round(float(v), 5) for v in weight[index]]
        for index in torch.nonzero(keep).flatten()
    }
    WEIGHTS_FILE.write_text(
        json.dumps(
            {
                "version": VERSION,
                "feature_dim": FEATURE_DIM,
                "labels": list(LABELS),
                "bias": [round(float(v), 5) for v in model.bias.detach()],
                "thresholds": {"urgent": urgent_threshold, "flag": flag_threshold},
                "training": {
                    "file": "ml/safety_eval/data/train.jsonl",
                    "seed": SEED,
                    "epochs": EPOCHS,
                    "learning_rate": LR,
                    "l2": L2,
                    "threshold_rule": f"lowest threshold with {FOLDS}-fold CV false-positive "
                    f"rate <= {MAX_URGENT_FPR} (urgent) / {MAX_FLAG_FPR} (flag)",
                },
                "weights": rows,
            },
            separators=(",", ":"),
        ),
        encoding="utf-8",
    )
    print(f"exported {len(rows)} weight rows to {WEIGHTS_FILE}")  # noqa: T201


def main() -> None:
    texts, labels = load()
    x, y = to_matrix(texts), torch.tensor(labels)
    urgent_threshold, flag_threshold = choose_thresholds(x, y)
    print(f"thresholds: urgent={urgent_threshold} flag={flag_threshold}")  # noqa: T201
    export(train(x, y), urgent_threshold, flag_threshold)


if __name__ == "__main__":
    main()
