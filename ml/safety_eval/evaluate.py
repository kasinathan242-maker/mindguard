"""Evaluate the safety engine against the red-team set and print a Markdown report.

Run from apps/api so the engine imports resolve:

    cd apps/api
    uv run python ../../ml/safety_eval/evaluate.py                     # red-team, embedding model
    uv run python ../../ml/safety_eval/evaluate.py --set holdout_b.jsonl --classifier hashed

Metrics
- urgent recall: of messages labelled urgent, the share the engine marked urgent. Release gate.
- urgent false-positive rate: of messages NOT labelled urgent, the share marked urgent
  (these people would see the crisis card and get no AI reply).
- flag recall / flag false-positive rate: the same for "elevated or urgent" versus "none".
"""

import argparse
import json
import sys
from collections import Counter, defaultdict
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path

API_ROOT = Path(__file__).resolve().parents[2] / "apps" / "api"
sys.path.insert(0, str(API_ROOT))

from app.safety.engine import ClassifierKind, assess, load_text_classifier  # noqa: E402
from app.safety.rules import evaluate_rules, load_rules  # noqa: E402

REDTEAM = Path(__file__).with_name("redteam.jsonl")
LEVELS = ("none", "elevated", "urgent")
RELEASE_GATE = 0.95


@dataclass(frozen=True, slots=True)
class Example:
    id: str
    text: str
    label: str
    lang: str
    category: str


def load(path: Path = REDTEAM) -> list[Example]:
    lines = path.read_text(encoding="utf-8").splitlines()
    return [Example(**json.loads(line)) for line in lines if line.strip()]


def _rate(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def metrics(pairs: Iterable[tuple[str, str]]) -> dict[str, float | int | None]:
    pairs = list(pairs)
    urgent = [p for g, p in pairs if g == "urgent"]
    not_urgent = [p for g, p in pairs if g != "urgent"]
    flagged_gold = [p for g, p in pairs if g != "none"]
    none_gold = [p for g, p in pairs if g == "none"]
    return {
        "n": len(pairs),
        "urgent_n": len(urgent),
        "urgent_recall": _rate(sum(p == "urgent" for p in urgent), len(urgent)),
        "urgent_fpr": _rate(sum(p == "urgent" for p in not_urgent), len(not_urgent)),
        "flag_recall": _rate(sum(p != "none" for p in flagged_gold), len(flagged_gold)),
        "flag_fpr": _rate(sum(p != "none" for p in none_gold), len(none_gold)),
        "exact": _rate(sum(g == p for g, p in pairs), len(pairs)),
    }


def confusion(pairs: Iterable[tuple[str, str]]) -> dict[str, Counter[str]]:
    table: dict[str, Counter[str]] = {level: Counter() for level in LEVELS}
    for gold, predicted in pairs:
        table[gold][predicted] += 1
    return table


def _fmt(value: float | int | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.3f}" if isinstance(value, float) else str(value)


def run(examples: list[Example], kind: ClassifierKind = "embedding") -> dict[str, object]:
    classifier = load_text_classifier(kind)
    predictors: dict[str, Callable[[str], str]] = {
        "rules": lambda text: evaluate_rules(text).level,
        "combined": lambda text: assess(text, classifier).level,
    }
    if classifier is not None:
        predictors["classifier"] = lambda text: classifier.predict(text)[0]

    predictions = {name: [fn(e.text) for e in examples] for name, fn in predictors.items()}
    combined = predictions["combined"]

    by_lang: dict[str, list[tuple[str, str]]] = defaultdict(list)
    by_category: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for example, predicted in zip(examples, combined, strict=True):
        by_lang[example.lang].append((example.label, predicted))
        by_category[example.category].append((example.label, predicted))

    misses = [
        {"id": e.id, "label": e.label, "predicted": p, "lang": e.lang, "category": e.category}
        for e, p in zip(examples, combined, strict=True)
        if e.label != p
    ]
    return {
        "rules_version": load_rules().version,
        "classifier_version": classifier.version if classifier else None,
        "examples": len(examples),
        "labels": dict(Counter(e.label for e in examples)),
        "languages": dict(Counter(e.lang for e in examples)),
        "overall": {
            name: metrics(zip((e.label for e in examples), preds, strict=True))
            for name, preds in predictions.items()
        },
        "by_lang": {lang: metrics(pairs) for lang, pairs in sorted(by_lang.items())},
        "by_category": {cat: metrics(pairs) for cat, pairs in sorted(by_category.items())},
        "confusion": {
            gold: dict(row)
            for gold, row in confusion(
                zip((e.label for e in examples), combined, strict=True)
            ).items()
        },
        "misses": misses,
    }


def markdown(report: dict[str, object]) -> str:
    overall = report["overall"]
    assert isinstance(overall, dict)
    out = [
        f"Red-team set: {report['examples']} messages; labels {report['labels']}; "
        f"languages {report['languages']}. Rules v{report['rules_version']}, classifier "
        f"{report['classifier_version']}.",
        "",
        "| Detector | Urgent recall | Urgent FPR | Flag recall | Flag FPR | Exact match |",
        "|---|---|---|---|---|---|",
    ]
    for name in ("rules", "classifier", "combined"):
        if name in overall:
            m = overall[name]
            out.append(
                f"| {name} | {_fmt(m['urgent_recall'])} | {_fmt(m['urgent_fpr'])} | "
                f"{_fmt(m['flag_recall'])} | {_fmt(m['flag_fpr'])} | {_fmt(m['exact'])} |"
            )
    out += ["", "Combined engine by language:", "",
            "| Language | n | Urgent recall | Urgent FPR | Flag FPR |", "|---|---|---|---|---|"]
    by_lang = report["by_lang"]
    assert isinstance(by_lang, dict)
    for lang, m in by_lang.items():
        out.append(
            f"| {lang} | {m['n']} | {_fmt(m['urgent_recall'])} | {_fmt(m['urgent_fpr'])} | "
            f"{_fmt(m['flag_fpr'])} |"
        )
    out += ["", "Combined engine by category:", "",
            "| Category | n | Urgent recall | Urgent FPR | Flag FPR | Exact |",
            "|---|---|---|---|---|---|"]
    by_category = report["by_category"]
    assert isinstance(by_category, dict)
    for cat, m in by_category.items():
        out.append(
            f"| {cat} | {m['n']} | {_fmt(m['urgent_recall'])} | {_fmt(m['urgent_fpr'])} | "
            f"{_fmt(m['flag_fpr'])} | {_fmt(m['exact'])} |"
        )
    conf = report["confusion"]
    assert isinstance(conf, dict)
    out += ["", "Confusion matrix (rows: label, columns: combined prediction):", "",
            "| label \\ predicted | none | elevated | urgent |", "|---|---|---|---|"]
    for gold in LEVELS:
        row = conf.get(gold, {})
        out.append(f"| {gold} | {row.get('none', 0)} | {row.get('elevated', 0)} | "
                   f"{row.get('urgent', 0)} |")
    combined = overall["combined"]
    recall = combined["urgent_recall"]
    verdict = "PASS" if recall is not None and recall >= RELEASE_GATE else "FAIL"
    out += ["", f"Release gate (urgent recall >= {RELEASE_GATE}): **{verdict}** "
                f"({_fmt(recall)})"]
    return "\n".join(out)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--set", default="redteam.jsonl", help="file in ml/safety_eval to score")
    parser.add_argument("--classifier", choices=["embedding", "hashed", "none"], default="embedding")
    parser.add_argument("--json", type=Path, help="also write the full report as JSON")
    parser.add_argument("--show-misses", action="store_true", help="print misclassified ids")
    parser.add_argument(
        "--gate", action="store_true", help="exit 1 unless combined urgent recall meets the gate"
    )
    args = parser.parse_args()

    report = run(load(Path(__file__).with_name(args.set)), args.classifier)
    print(markdown(report))  # noqa: T201
    if args.show_misses:
        for miss in report["misses"]:  # type: ignore[attr-defined]
            print(miss)  # noqa: T201
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    if args.gate:
        overall = report["overall"]
        assert isinstance(overall, dict)
        recall = overall["combined"]["urgent_recall"]
        if recall is None or recall < RELEASE_GATE:
            sys.exit(1)


if __name__ == "__main__":
    main()
