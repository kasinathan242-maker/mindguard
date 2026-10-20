import json
import logging

import pytest

from app.core.logging import JsonFormatter, PiiScrubFilter, scrub


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("contact me at priya.k+1@example.co.in", "contact me at [email]"),
        ("call +91 98765 43210 now", "call [phone] now"),
        ("my number is 9876543210", "my number is [phone]"),
        ("score was 14 on 2026-10-20", "score was 14 on 2026-10-20"),
    ],
)
def test_scrub_redacts_contact_details_only(raw: str, expected: str) -> None:
    assert scrub(raw) == expected


def test_formatter_emits_json_with_scrubbed_message_and_extras() -> None:
    record = logging.makeLogRecord(
        {
            "name": "test",
            "levelno": logging.INFO,
            "levelname": "INFO",
            "msg": "user %s signed in",
            "args": ("a@b.com",),
            "route": "/api/v1/auth/login",
            "note": "reach me on 9876543210",
        }
    )
    PiiScrubFilter().filter(record)

    payload = json.loads(JsonFormatter().format(record))

    assert payload["msg"] == "user [email] signed in"
    assert payload["route"] == "/api/v1/auth/login"
    assert payload["note"] == "reach me on [phone]"
    assert payload["level"] == "INFO"
