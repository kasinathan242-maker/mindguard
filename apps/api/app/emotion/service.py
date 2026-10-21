import logging
from typing import Protocol

from app.emotion.model import EmotionResult

logger = logging.getLogger(__name__)


class EmotionPredictor(Protocol):
    def predict(self, text: str) -> EmotionResult: ...


def load_optional_emotion_model(enabled: bool) -> EmotionPredictor | None:
    """The emotion model is optional: chat works without it, and a load failure never breaks it."""
    if not enabled:
        return None
    try:
        from app.emotion.model import load_emotion_model  # imports torch lazily

        return load_emotion_model()
    except (OSError, ImportError, ValueError):
        logger.warning("emotion model unavailable; chat continues without emotion hints")
        return None
