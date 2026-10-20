import json
import re
from datetime import date, timedelta
from pathlib import Path

import pytest
from httpx import AsyncClient

from app.safety.resources import MAX_AGE_DAYS, load_resources

WEB_FALLBACK = (
    Path(__file__).resolve().parents[2] / "web" / "src" / "features" / "crisis" / "fallback.json"
)

# Claims we cannot guarantee on behalf of a third-party service.
FORBIDDEN_CLAIMS = re.compile(r"confidential|anonymous|no police|untraceable|private", re.I)


def test_every_resource_was_verified_within_180_days() -> None:
    """Release gate: CI fails when any crisis resource has not been re-checked recently."""
    cutoff = date.today() - timedelta(days=MAX_AGE_DAYS)
    stale = [r.id for r in load_resources().resources if r.last_verified < cutoff]
    assert stale == [], f"re-verify and update last_verified for: {stale}"


def test_resources_include_tele_manas_and_emergency() -> None:
    by_id = {r.id: r for r in load_resources().resources}
    assert by_id["tele_manas"].dial == "14416"
    assert by_id["tele_manas"].alternate_dial == "18008914416"
    assert by_id["emergency_112"].dial == "112"


def test_dial_strings_are_digits_only() -> None:
    for r in load_resources().resources:
        assert r.dial.isdigit()
        assert r.alternate_dial is None or r.alternate_dial.isdigit()


@pytest.mark.parametrize("locale", ["en", "ta"])
def test_no_resource_promises_confidentiality(locale: str) -> None:
    for r in load_resources().resources:
        text = r.description.get(locale)  # type: ignore[arg-type]
        assert not FORBIDDEN_CLAIMS.search(text), (r.id, locale)


def test_web_offline_fallback_matches_the_reviewed_file() -> None:
    """The crisis card must work with no network, so the web app bundles a copy of the numbers."""
    fallback = json.loads(WEB_FALLBACK.read_text(encoding="utf-8"))
    expected = {
        locale: [
            {
                "id": r.id,
                "kind": r.kind,
                "name": r.name.get(locale),
                "description": r.description.get(locale),
                "display_number": r.display_number,
                "dial": r.dial,
                "alternate_display_number": r.alternate_display_number,
                "alternate_dial": r.alternate_dial,
            }
            for r in load_resources().resources
        ]
        for locale in ("en", "ta")
    }
    assert fallback == expected, "regenerate with: uv run python -m app.safety.export_fallback"


async def test_resources_endpoint_is_public_and_localised(client: AsyncClient) -> None:
    en = await client.get("/api/v1/safety/resources")
    ta = await client.get("/api/v1/safety/resources", params={"locale": "ta"})

    assert en.status_code == ta.status_code == 200
    assert en.json()[0]["name"] == "Tele-MANAS"
    assert "டெலி-மனஸ்" in ta.json()[0]["name"]
    assert "max-age" in en.headers["cache-control"]
