"""Mood patterns: how mood moves with sleep and steps. Shown as "patterns, not causes"."""

import math
from collections import defaultdict
from datetime import date

from pydantic import BaseModel

MIN_POINTS = 14


class Pattern(BaseModel):
    metric: str
    points: int
    correlation: float | None  # Pearson r; None when there are too few days
    strength: str  # "not enough data" | "none" | "weak" | "moderate" | "strong"


def pearson(xs: list[float], ys: list[float]) -> float | None:
    n = len(xs)
    if n < 2:
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    sx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    sy = math.sqrt(sum((y - my) ** 2 for y in ys))
    if sx == 0 or sy == 0:
        return None
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys, strict=True)) / (sx * sy)


def describe(r: float | None, points: int) -> str:
    if points < MIN_POINTS or r is None:
        return "not enough data"
    size = abs(r)
    if size < 0.1:
        return "none"
    if size < 0.3:
        return "weak"
    return "moderate" if size < 0.5 else "strong"


def mood_patterns(
    mood_by_day: dict[date, float], metrics: dict[str, dict[date, float]]
) -> list[Pattern]:
    out = []
    for metric, values in metrics.items():
        days = sorted(set(mood_by_day) & set(values))
        r = pearson([values[d] for d in days], [mood_by_day[d] for d in days])
        enough = len(days) >= MIN_POINTS
        out.append(
            Pattern(
                metric=metric,
                points=len(days),
                correlation=round(r, 2) if enough and r is not None else None,
                strength=describe(r, len(days)),
            )
        )
    return out


def daily_mean(pairs: list[tuple[date, float]]) -> dict[date, float]:
    buckets: dict[date, list[float]] = defaultdict(list)
    for day, value in pairs:
        buckets[day].append(value)
    return {day: sum(v) / len(v) for day, v in buckets.items()}
