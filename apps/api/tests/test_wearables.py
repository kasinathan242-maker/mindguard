import pytest
from httpx import AsyncClient

from app.integrations.wearables import InvalidFileError, parse_csv
from tests.helpers import start_anonymous

GOOD = b"day,sleep_minutes,steps,resting_hr\n2026-10-01,420,6500,64\n2026-10-02,,4100,\n"


def test_parser_accepts_daily_aggregates_with_blanks() -> None:
    rows = parse_csv(GOOD)
    assert len(rows) == 4
    assert {m for _, m, _ in rows} == {"sleep_minutes", "steps", "resting_hr"}


@pytest.mark.parametrize(
    ("raw", "message"),
    [
        (b"date,sleep,steps\n2026-10-01,1,2\n", "header"),
        (b"day,sleep_minutes,steps,resting_hr\n01/10/2026,420,1,60\n", "YYYY-MM-DD"),
        (b"day,sleep_minutes,steps,resting_hr\n2026-10-01,2000,1,60\n", "between"),
        (b"day,sleep_minutes,steps,resting_hr\n2026-10-01,400,abc,60\n", "number"),
        (b"day,sleep_minutes,steps,resting_hr\n2026-10-01,400,1,60\n2026-10-01,1,1,60\n", "twice"),
        (b"day,sleep_minutes,steps,resting_hr\n2999-01-01,400,1,60\n", "future"),
        (b"day,sleep_minutes,steps,resting_hr\n", "no data"),
        (b"\xff\xfe\x00", "UTF-8"),
    ],
)
def test_parser_rejects_bad_files(raw: bytes, message: str) -> None:
    with pytest.raises(InvalidFileError, match=message):
        parse_csv(raw)


def test_parser_rejects_oversized_files() -> None:
    with pytest.raises(InvalidFileError, match="larger"):
        parse_csv(b"x" * (600 * 1024))


async def test_import_needs_consent_then_works_and_revoking_deletes(client: AsyncClient) -> None:
    await start_anonymous(client)
    files = {"file": ("health.csv", GOOD, "text/csv")}
    blocked = await client.post("/api/v1/integrations/wearables/import", files=files)
    assert blocked.status_code == 403

    await client.put("/api/v1/consents", json={"consents": {"wearables": True}})
    imported = await client.post("/api/v1/integrations/wearables/import", files=files)
    assert imported.json() == {"days": 2, "values": 4}
    again = await client.post("/api/v1/integrations/wearables/import", files=files)
    assert again.json()["values"] == 4
    assert len((await client.get("/api/v1/integrations/wearables")).json()) == 4

    export = (await client.get("/api/v1/privacy/export")).json()
    assert len(export["wearables"]) == 4

    await client.put("/api/v1/consents", json={"consents": {"wearables": False}})
    await client.put("/api/v1/consents", json={"consents": {"wearables": True}})
    assert (await client.get("/api/v1/integrations/wearables")).json() == []


async def test_non_csv_uploads_are_refused(client: AsyncClient) -> None:
    await start_anonymous(client, {"core": True, "wearables": True})
    response = await client.post(
        "/api/v1/integrations/wearables/import",
        files={"file": ("x.exe", b"MZ", "application/x-msdownload")},
    )
    assert response.status_code == 415
