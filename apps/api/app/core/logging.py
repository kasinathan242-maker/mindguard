"""Structured JSON logging with PII scrubbing.

Mental-health data must never reach logs. Handlers log identifiers and outcomes, not content,
and this filter is a second line of defence that redacts emails and phone numbers that slip
into a message or its arguments.
"""

import json
import logging
import re
import sys
from datetime import UTC, datetime
from typing import Any

_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_PHONE_CANDIDATE = re.compile(r"(?<!\d)\+?\d[\d\s-]{8,}\d(?!\d)")
_MIN_PHONE_DIGITS = 10  # Indian mobiles have 10; shorter runs are dates, scores or counts

_RESERVED = frozenset(vars(logging.makeLogRecord({})).keys()) | {"message", "asctime"}


def _redact_phone(match: re.Match[str]) -> str:
    digits = sum(ch.isdigit() for ch in match.group())
    return "[phone]" if digits >= _MIN_PHONE_DIGITS else match.group()


def scrub(text: str) -> str:
    return _PHONE_CANDIDATE.sub(_redact_phone, _EMAIL.sub("[email]", text))


class PiiScrubFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = scrub(record.getMessage())
        record.args = None
        return True


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        for key, value in vars(record).items():
            if key not in _RESERVED and not key.startswith("_"):
                payload[key] = scrub(value) if isinstance(value, str) else value
        if record.exc_info:
            payload["exc"] = scrub(self.formatException(record.exc_info))
        return json.dumps(payload, default=str)


def configure_logging(level: str) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    handler.addFilter(PiiScrubFilter())

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)

    # Access logs include full request paths; we keep them, since paths never carry personal data
    # by design, but route them through the same scrubbing handler.
    for name in ("uvicorn", "uvicorn.access", "uvicorn.error"):
        logger = logging.getLogger(name)
        logger.handlers = []
        logger.propagate = True
