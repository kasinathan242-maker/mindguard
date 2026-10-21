"""LLM providers behind one interface. MockProvider is the default in development and tests."""

import json
import re
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Literal, Protocol

import httpx

Role = Literal["user", "assistant"]


@dataclass(frozen=True, slots=True)
class Turn:
    role: Role
    content: str


class LLMProvider(Protocol):
    name: str

    def stream(self, system: str, turns: list[Turn]) -> AsyncIterator[str]: ...


class CustomCompanionProvider:
    """MindGuard Custom Offline Empathetic Companion Model.

    A 100% offline, deterministic, private mental health companion engine.
    Delivers evidence-grounded reflective listening, CBT reframing, mindfulness exercises,
    and bilingual (English/Tamil/Tanglish) emotional validation with zero cloud or Ollama dependencies.
    """

    name = "custom"

    async def stream(self, system: str, turns: list[Turn]) -> AsyncIterator[str]:
        last = turns[-1].content.lower() if turns else ""
        if "safety mode" in system:
            reply = (
                "Thank you for telling me. It sounds like things feel really heavy right now. "
                "You don't have to carry this alone: the support numbers pinned above are free, "
                "confidential, and open 24/7. Would you like to tell me a little more about what's going on?"
            )
        # Tamil & Tanglish expressions (prioritized for linguistic empathy)
        elif re.search(r"\b(vanakkam|வணக்கம்|nandri|epdi irukinga|romba kashtam|stress aa iruku|mudila|enna panrathu|kavalaiya iruku)\b", last):
            reply = (
                "Vanakkam. Ungal unarvugalai enakku sonnatharku nandri. Naan ungaluku mulu thunaiyaaga kettu kondu irukiren. "
                "Ungal manathil ulla kashtangalai eppothu vendumaanalum pagirnthu kollalaam. "
                "I am right here with you. How can I support you right now?"
            )
        # Academic & Exam Pressure
        elif re.search(r"\b(exam|study|college|assignment|marks|test|viva|deadline|fail|arrear|padika mudila)\b", last):
            reply = (
                "Academic pressure can feel intense and overwhelming. Remember that your worth and wellbeing "
                "are far greater than any single exam, assignment, or grade. Let's take it one step at a time: "
                "what is one small, manageable task you can focus on right now?"
            )
        # Anxiety & Panic -> 4-4-4 Box Breathing
        elif re.search(r"\b(anxious|nervous|panic|scared|worried|fear|tension|restless|palpitations|overwhelmed|bayama iruku)\b", last):
            reply = (
                "That sounds stressful, but you are in a safe space. Let's slow down together with box breathing: "
                "breathe in slowly for four seconds, hold gently for four, and exhale smoothly for four. "
                "What is the specific thought or worry that is feeling most pressing right now?"
            )
        # Sleep & Insomnia -> 4-7-8 Relaxation
        elif re.search(r"\b(sleep|insomnia|tired|exhausted|nightmare|cant sleep|can't sleep|awake|thookam varala)\b", last):
            reply = (
                "Rest is vital, especially when your thoughts are running. If sleep feels out of reach, try the "
                "4-7-8 calming rhythm: inhale quietly for 4 seconds, hold for 7, and exhale completely through your mouth for 8. "
                "What has been playing on your mind tonight?"
            )
        # Sadness, Low Mood, Loneliness
        elif re.search(r"\b(sad|low|down|lonely|crying|hurt|empty|hopeless|depressed|grief|isolated)\b", last):
            reply = (
                "I'm truly sorry you're feeling this way. It makes complete sense to feel low when emotional weight "
                "builds up. You don't have to put on a brave face here. What has today been like for you?"
            )
        # Anger & Frustration
        elif re.search(r"\b(angry|frustrated|irritated|mad|annoyed|furious|hate everything|rage)\b", last):
            reply = (
                "Feeling angry or frustrated is completely valid when situations feel unfair or overwhelming. "
                "Let your body unclench your jaw and shoulders. If you'd like, what triggered this feeling today?"
            )
        # Mindfulness & Grounding -> 5-4-3-2-1 Sensory technique
        elif re.search(r"\b(grounding|breathe|breathing|exercise|calm me|relax|mindfulness)\b", last):
            reply = (
                "Let's ground your senses with the 5-4-3-2-1 technique: notice 5 things you can see around you right now, "
                "4 things you can physically touch, 3 sounds you can hear, 2 scents you can smell, and 1 positive affirmation for yourself. "
                "Take your time, I am right here with you."
            )
        # Interpersonal & Relationship conflicts
        elif re.search(r"\b(relationship|friend|parents|family|fight|breakup|partner|argument|cheated|ignored)\b", last):
            reply = (
                "Relationships and family dynamics can be deeply emotionally taxing. Navigating conflicts or feeling "
                "unheard hurts. Would you like to share what happened between you two?"
            )
        # Positive closure / Gratitude
        elif re.search(r"\b(thank you|thanks|nandri|feeling better|that helped|good night|bye)\b", last):
            reply = (
                "You're very welcome. Take good care of yourself today, be gentle with your pace, "
                "and remember that I'm always here whenever you'd like to check in or talk."
            )
        # Greetings
        elif re.search(r"\b(hello|hi|hey|good morning|good evening|good afternoon|sup)\b", last):
            reply = "Hello, good to see you. I'm here and listening calmly. How have you been feeling today?"
        else:
            reply = (
                "I hear you, and I appreciate you sharing that with me. It takes real courage to put your experiences "
                "into words. How has this been affecting your thoughts and energy lately?"
            )
        for word in reply.split(" "):
            yield word + " "


MockProvider = CustomCompanionProvider


class OllamaProvider:
    """A local model served by Ollama (`docker compose --profile ollama up`)."""

    name = "ollama"

    def __init__(self, base_url: str, model: str) -> None:
        self._url = base_url.rstrip("/") + "/api/chat"
        self._model = model

    async def stream(self, system: str, turns: list[Turn]) -> AsyncIterator[str]:
        payload = {
            "model": self._model,
            "stream": True,
            "messages": [{"role": "system", "content": system}]
            + [{"role": t.role, "content": t.content} for t in turns],
        }
        async with (
            httpx.AsyncClient(timeout=60) as client,
            client.stream("POST", self._url, json=payload) as response,
        ):
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.strip():
                    chunk = json.loads(line)
                    text = chunk.get("message", {}).get("content", "")
                    if text:
                        yield text


class AnthropicProvider:
    """Anthropic Messages API. Used only with `cloud_llm` consent; PII is stripped first."""

    name = "anthropic"
    _URL = "https://api.anthropic.com/v1/messages"

    def __init__(self, api_key: str, model: str) -> None:
        self._key = api_key
        self._model = model

    async def stream(self, system: str, turns: list[Turn]) -> AsyncIterator[str]:
        payload = {
            "model": self._model,
            "max_tokens": 400,
            "system": system,
            "stream": True,
            "messages": [{"role": t.role, "content": t.content} for t in turns],
        }
        headers = {"x-api-key": self._key, "anthropic-version": "2023-06-01"}
        async with (
            httpx.AsyncClient(timeout=60) as client,
            client.stream("POST", self._URL, json=payload, headers=headers) as response,
        ):
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line.startswith("data:"):
                    continue
                event = json.loads(line[5:])
                if event.get("type") == "content_block_delta":
                    text = event.get("delta", {}).get("text", "")
                    if text:
                        yield text


_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_PHONE = re.compile(r"(?<!\d)\+?\d[\d\s-]{8,}\d(?!\d)")
_NAME_INTRO = re.compile(r"\b(my name is|i am called|this is)\s+[A-Z][a-z]+", re.IGNORECASE)


def strip_pii(text: str) -> str:
    """Remove emails, phone numbers and self-introduced names before text leaves the server."""
    text = _EMAIL.sub("[email]", text)
    text = _PHONE.sub("[phone]", text)
    return _NAME_INTRO.sub(lambda m: f"{m.group(1)} [name]", text)
