import pytest

from app.emotion.model import EKMAN, is_tamil_or_tanglish
from app.emotion.service import load_optional_emotion_model


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("I feel anxious about my exam", False),
        ("எனக்கு பயமா இருக்கு", True),
        ("romba kashtam da, enna panna", True),
        ("da", False),
    ],
)
def test_tamil_and_tanglish_are_detected_as_unsupported(text: str, expected: bool) -> None:
    assert is_tamil_or_tanglish(text) is expected


def test_mapping_covers_all_goemotions_labels() -> None:
    assert len(EKMAN) == 28
    assert set(EKMAN.values()) == {
        "anger",
        "disgust",
        "fear",
        "joy",
        "sadness",
        "surprise",
        "neutral",
    }


def test_disabled_model_loads_nothing() -> None:
    assert load_optional_emotion_model(False) is None


@pytest.mark.model
def test_model_paths_when_weights_are_cached() -> None:
    from huggingface_hub import try_to_load_from_cache

    from app.emotion.model import MODEL, REVISION, load_emotion_model

    if not isinstance(try_to_load_from_cache(MODEL, "config.json", revision=REVISION), str):
        pytest.skip("emotion model not downloaded")
    model = load_emotion_model()
    assert model.predict("I am so happy today, thank you!").label == "joy"
    assert model.predict("romba kashtam da, enna panna").label == "unsupported"
    assert model.predict("ok").label in {"uncertain", "neutral"}
