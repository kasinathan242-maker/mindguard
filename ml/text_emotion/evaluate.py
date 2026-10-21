"""Evaluate the text emotion model on the held-out GoEmotions test split.

    cd apps/api
    uv run python ../../ml/text_emotion/evaluate.py

GoEmotions (Apache-2.0) labels are mapped to Ekman groups; only test examples whose labels map
to exactly one group are scored (multi-emotion examples have no single right answer). The model
was trained on the GoEmotions train split, so the test split is unseen.

Also reports a VADER baseline on a 3-way polarity version of the same examples
(joy = positive; anger, disgust, fear, sadness = negative; neutral), with the model collapsed the
same way, plus CPU latency per message.
"""

import json
import statistics
import sys
import time
from collections import Counter
from pathlib import Path

import pyarrow.parquet as pq
from huggingface_hub import hf_hub_download
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

API_ROOT = Path(__file__).resolve().parents[2] / "apps" / "api"
sys.path.insert(0, str(API_ROOT))

from app.emotion.model import CONFIDENCE_THRESHOLD, EKMAN, EmotionModel  # noqa: E402

DATASET = "google-research-datasets/go_emotions"
DATASET_REVISION = "add492243ff905527e67aeb8b80c082af02207c3"
GO_LABELS = (
    "admiration amusement anger annoyance approval caring confusion curiosity desire "
    "disappointment disapproval disgust embarrassment excitement fear gratitude grief joy love "
    "nervousness optimism pride realization relief remorse sadness surprise neutral"
).split()
GROUPS = ["anger", "disgust", "fear", "joy", "sadness", "surprise", "neutral"]
POLARITY = {"joy": "positive", "neutral": "neutral"} | dict.fromkeys(
    ["anger", "disgust", "fear", "sadness"], "negative"
)
REPORT = Path(__file__).with_name("report.json")


def f1_table(gold: list[str], pred: list[str], labels: list[str]) -> dict[str, float]:
    scores = {}
    for label in labels:
        tp = sum(g == p == label for g, p in zip(gold, pred, strict=True))
        fp = sum(p == label != g for g, p in zip(gold, pred, strict=True))
        fn = sum(g == label != p for g, p in zip(gold, pred, strict=True))
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        scores[label] = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return scores


def main() -> None:
    path = hf_hub_download(
        DATASET, "simplified/test-00000-of-00001.parquet", repo_type="dataset",
        revision=DATASET_REVISION,
    )
    table = pq.read_table(path).to_pylist()
    examples = []
    for row in table:
        groups = {EKMAN[GO_LABELS[i]] for i in row["labels"]}
        if len(groups) == 1:
            examples.append((row["text"], groups.pop()))

    model = EmotionModel()
    gold = [g for _, g in examples]
    texts = [t for t, _ in examples]
    preds: list[str] = []
    confidences: list[float] = []
    for start in range(0, len(texts), 64):
        for scores in model.group_scores(texts[start : start + 64]):
            label, conf = max(scores.items(), key=lambda item: item[1])
            preds.append(label)
            confidences.append(conf)

    per_class = f1_table(gold, preds, GROUPS)
    confident = [i for i, c in enumerate(confidences) if c >= CONFIDENCE_THRESHOLD]
    confident_f1 = f1_table([gold[i] for i in confident], [preds[i] for i in confident], GROUPS)

    vader = SentimentIntensityAnalyzer()
    gold_pol = [POLARITY[g] for g in gold if g != "surprise"]
    keep = [i for i, g in enumerate(gold) if g != "surprise"]
    model_pol = [POLARITY.get(preds[i], "neutral") for i in keep]
    vader_pol = []
    for i in keep:
        compound = vader.polarity_scores(texts[i])["compound"]
        vader_pol.append("positive" if compound >= 0.05 else "negative" if compound <= -0.05 else "neutral")
    pols = ["positive", "negative", "neutral"]

    latencies = []
    for text in texts[:200]:
        start = time.perf_counter()
        model.predict(text)
        latencies.append((time.perf_counter() - start) * 1000)
    latencies.sort()

    confusion = {g: dict(Counter(p for gg, p in zip(gold, preds, strict=True) if gg == g)) for g in GROUPS}
    report = {
        "dataset": f"{DATASET}@{DATASET_REVISION[:8]} test split, single-group examples",
        "examples": len(examples),
        "label_counts": dict(Counter(gold)),
        "macro_f1": round(statistics.mean(per_class.values()), 3),
        "per_class_f1": {k: round(v, 3) for k, v in per_class.items()},
        "accuracy": round(sum(g == p for g, p in zip(gold, preds, strict=True)) / len(gold), 3),
        "confidence_threshold": CONFIDENCE_THRESHOLD,
        "coverage_above_threshold": round(len(confident) / len(gold), 3),
        "macro_f1_above_threshold": round(statistics.mean(confident_f1.values()), 3),
        "polarity_macro_f1": {
            "model": round(statistics.mean(f1_table(gold_pol, model_pol, pols).values()), 3),
            "vader_baseline": round(statistics.mean(f1_table(gold_pol, vader_pol, pols).values()), 3),
        },
        "latency_ms": {
            "median": round(statistics.median(latencies), 1),
            "p95": round(latencies[int(len(latencies) * 0.95)], 1),
        },
        "confusion": confusion,
    }
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "confusion"}, indent=2))  # noqa: T201


if __name__ == "__main__":
    main()
