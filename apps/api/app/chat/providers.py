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


class MockProvider:
    """Deterministic, offline replies for development, tests and demos without a model.

    It is a fixture, not a therapist: replies are short reflective prompts chosen by simple cues.
    """

    name = "mock"

    async def stream(self, system: str, turns: list[Turn]) -> AsyncIterator[str]:
        last = turns[-1].content.lower() if turns else ""
        if "safety mode" in system:
            reply = (
                "Thank you for telling me. It sounds like things feel really heavy right now. "
                "You don't have to carry this alone: the support numbers pinned above are free "
                "and open all day. Would you like to tell me a little more about what's going on?"
            )
        elif re.search(r"\b(anxious|nervous|panic|scared|worried)\b", last):
            reply = (
                "That sounds stressful. Let's slow down together: breathe in for four, hold for "
                "four, out for four. What's the part that worries you most right now?"
            )
        elif re.search(r"\b(sad|low|down|lonely|tired)\b", last):
            reply = (
                "I'm sorry you're feeling this way. It makes sense to feel low when things pile "
                "up. What has today been like for you?"
            )
        else:
            reply = "I'm here and listening. How have you been feeling today?"
        for word in reply.split(" "):
            yield word + " "


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
