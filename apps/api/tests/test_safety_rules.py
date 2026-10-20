import pytest

from app.safety.normalize import clauses, normalize
from app.safety.rules import evaluate_rules, load_rules


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("I'm SOOO tired", "i am soo tired"),
        ("dont wanna", "do not want to"),
        ("kms", "kill myself"),
        ("haha \U0001f602", "haha lol"),
        ("my self", "myself"),
    ],
)
def test_normalize(raw: str, expected: str) -> None:
    assert normalize(raw) == expected


def test_clauses_split_on_but_and_sentence_breaks() -> None:
    assert clauses("i will never do it but i want to die. ok") == [
        "i will never do it",
        "i want to die",
        "ok",
    ]


def test_rule_file_is_valid_and_ids_are_unique() -> None:
    rules = load_rules()
    ids = [r.spec.id for r in rules.rules]
    assert len(ids) == len(set(ids))
    assert {r.spec.lang for r in rules.rules} == {"en", "ta", "tanglish"}
    assert rules.version >= 1


@pytest.mark.parametrize(
    "text",
    [
        "I want to kill myself",
        "i dont want to live anymore",
        "everyone would be better off without me",
        "how many paracetamol would it take",
        "by the time you read this i will be gone",
        "I've been cutting myself again",
        "what's the point of living",
        "I failed my exams and I want to die",  # exam stress must never soften intent
        "honestly death sounds like a relief",
        "நான் தற்கொலை பண்ணப் போறேன்",
        "சாகப் போறேன்",
        "enakku saaganum da",
        "vaazha pudikala",
        "ellarukkum bye",
        "lol but seriously i want to die",
    ],
)
def test_urgent(text: str) -> None:
    assert evaluate_rules(text).level == "urgent"


@pytest.mark.parametrize(
    ("text", "adjustment"),
    [
        ("I would never kill myself, I'm just tired", "negated"),
        ("i'm not planning to die but i think about it", "negated"),
        ("naan saaga maaten", None),
        ("my friend said she wants to kill herself", None),
        ("en friend saaga poren nu text panna", "third_party"),
        ("someone in our hostel was talking about jumping off the terrace", "third_party"),
        ("I used to want to die but I'm better now", "remission"),
        ("this song goes 'i want to die tonight'", "quotation"),
        ("i want to die lol exam tomorrow", "hyperbole"),
    ],
)
def test_context_softens_to_elevated(text: str, adjustment: str | None) -> None:
    result = evaluate_rules(text)
    assert result.level == "elevated"
    if adjustment is not None:
        assert adjustment in {hit.adjustment for hit in result.hits}


@pytest.mark.parametrize(
    "text",
    [
        "this exam is killing me lol",
        "kill me now this lecture is so boring",
        "dying to watch the new movie",
        "I'm going to die of embarrassment",
        "my phone is dead",
        "this traffic will be the death of me",
        "suicide rates among students in india",
        "I want to end my gym membership",
        "my grandmother who died last year",
        "exam la saavadichitaanga",
        "had a good day today!",
    ],
)
def test_none(text: str) -> None:
    assert evaluate_rules(text).level == "none"


def test_no_rule_lets_negation_cancel_its_own_words() -> None:
    # "no longer want" is both the urgent phrase and a remission phrase; it must stay urgent.
    assert evaluate_rules("i no longer want to live").level == "urgent"
    # A negation in another clause does not cancel this one.
    assert evaluate_rules("i won't do anything but i want to die").level == "urgent"


def test_plans_stay_urgent_under_jokes_and_quotes() -> None:
    assert evaluate_rules("haha i'm fine. i've just been saving pills").level == "urgent"
    assert evaluate_rules("like in the movie, i'm going to jump off the bridge").level == "urgent"


def test_results_carry_rule_ids_not_text() -> None:
    result = evaluate_rules("I want to kill myself")
    assert result.rule_ids
    assert all("." in rule_id for rule_id in result.rule_ids)
    assert all("kill myself" not in rule_id for rule_id in result.rule_ids)
