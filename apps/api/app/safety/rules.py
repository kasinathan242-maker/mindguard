"""Layer 1 of the safety engine: curated multilingual patterns from `patterns.yaml`."""

import re
from dataclasses import dataclass, field, fields
from functools import lru_cache
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel

from app.safety.normalize import clauses, normalize

PATTERNS_FILE = Path(__file__).with_name("patterns.yaml")

Level = Literal["none", "elevated", "urgent"]
_RANK: dict[Level, int] = {"none": 0, "elevated": 1, "urgent": 2}


def max_level(a: Level, b: Level) -> Level:
    return a if _RANK[a] >= _RANK[b] else b


class RuleSpec(BaseModel):
    id: str
    level: Literal["elevated", "urgent"]
    category: str
    lang: Literal["en", "ta", "tanglish"]
    pattern: str
    downgradable: bool = True
    hyperbole: bool = False


class Modifiers(BaseModel):
    benign: list[str]
    negation_before: list[str]
    negation_after: list[str]
    third_party: list[str]
    reported_speech_after: list[str]
    quotation: list[str]
    informational: list[str]
    hyperbole: list[str]
    sincerity: list[str]
    everyday_stress: list[str]
    remission: list[str]


class PatternFile(BaseModel):
    version: int
    rules: list[RuleSpec]
    modifiers: Modifiers


Patterns = tuple[re.Pattern[str], ...]


@dataclass(frozen=True, slots=True)
class CompiledModifiers:
    benign: Patterns
    negation_before: Patterns
    negation_after: Patterns
    third_party: Patterns
    reported_speech_after: Patterns
    quotation: Patterns
    informational: Patterns
    hyperbole: Patterns
    sincerity: Patterns
    everyday_stress: Patterns
    remission: Patterns


@dataclass(frozen=True, slots=True)
class CompiledRule:
    spec: RuleSpec
    regex: re.Pattern[str]


@dataclass(frozen=True, slots=True)
class RuleSet:
    version: int
    rules: tuple[CompiledRule, ...]
    modifiers: CompiledModifiers


@dataclass(frozen=True, slots=True)
class RuleHit:
    rule_id: str
    category: str
    level: Level
    # Why the level differs from the rule's own level, if it does.
    adjustment: str | None = None


@dataclass(frozen=True, slots=True)
class RuleResult:
    level: Level
    hits: tuple[RuleHit, ...] = field(default_factory=tuple)

    @property
    def rule_ids(self) -> list[str]:
        return [hit.rule_id for hit in self.hits]


@lru_cache
def load_rules(path: Path = PATTERNS_FILE) -> RuleSet:
    raw = PatternFile.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
    ids = [r.id for r in raw.rules]
    duplicates = sorted({i for i in ids if ids.count(i) > 1})
    if duplicates:
        raise ValueError(f"duplicate rule ids in patterns.yaml: {duplicates}")
    compiled = {
        f.name: tuple(re.compile(p) for p in getattr(raw.modifiers, f.name))
        for f in fields(CompiledModifiers)
    }
    return RuleSet(
        version=raw.version,
        rules=tuple(CompiledRule(spec=r, regex=re.compile(r.pattern)) for r in raw.rules),
        modifiers=CompiledModifiers(**compiled),
    )


def _any(patterns: Patterns, text: str) -> bool:
    return any(p.search(text) for p in patterns)


def _starts(patterns: Patterns, text: str) -> bool:
    return any(p.match(text) for p in patterns)


def _adjust(
    rule: CompiledRule,
    clause: str,
    match: re.Match[str],
    mods: CompiledModifiers,
    doc: dict[str, bool],
) -> RuleHit:
    spec = rule.spec
    before = clause[: match.start()]
    after = clause[match.end() :]
    # Clause context without the matched words, so a phrase can never modify itself
    # ("i no longer want to live" must not count as remission).
    around = f"{before} {after}"

    if spec.level == "urgent":
        if _any(mods.negation_before, before) or _starts(mods.negation_after, after):
            return RuleHit(spec.id, spec.category, "elevated", "negated")
        # Someone else's plan is still worrying, but it is not this person's crisis.
        if _any(mods.third_party, before) or _starts(mods.reported_speech_after, after):
            return RuleHit(spec.id, spec.category, "elevated", "third_party")
        if spec.downgradable:
            if _any(mods.remission, around):
                return RuleHit(spec.id, spec.category, "elevated", "remission")
            if doc["quotation"]:
                return RuleHit(spec.id, spec.category, "elevated", "quotation")
            if doc["informational"]:
                return RuleHit(spec.id, spec.category, "elevated", "informational")
            if doc["hyperbole"]:
                return RuleHit(spec.id, spec.category, "elevated", "hyperbole")
        return RuleHit(spec.id, spec.category, "urgent")

    if spec.category == "topic" and doc["informational"]:
        return RuleHit(spec.id, spec.category, "none", "informational")
    if spec.hyperbole and (doc["hyperbole"] or doc["everyday_stress"]):
        return RuleHit(spec.id, spec.category, "none", "hyperbole")
    return RuleHit(spec.id, spec.category, "elevated")


def _strip_benign(text: str, mods: CompiledModifiers) -> str:
    for pattern in mods.benign:
        text = pattern.sub(" ", text)
    return text


def evaluate_rules(text: str, rule_set: RuleSet | None = None) -> RuleResult:
    rs = rule_set or load_rules()
    mods = rs.modifiers
    normalised = _strip_benign(normalize(text), mods)
    if not normalised.strip():
        return RuleResult("none")
    doc = {
        "quotation": _any(mods.quotation, normalised),
        "informational": _any(mods.informational, normalised),
        # "lol but seriously" is not a joke.
        "hyperbole": _any(mods.hyperbole, normalised) and not _any(mods.sincerity, normalised),
        "everyday_stress": _any(mods.everyday_stress, normalised),
    }

    level: Level = "none"
    hits: list[RuleHit] = []
    for clause in clauses(normalised):
        for rule in rs.rules:
            for match in rule.regex.finditer(clause):
                hit = _adjust(rule, clause, match, mods, doc)
                hits.append(hit)
                level = max_level(level, hit.level)
    return RuleResult(level=level, hits=tuple(hits))
