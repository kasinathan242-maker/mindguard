from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import inspect, select

from app.core.resources import Resources
from app.safety.models import SafetyEvent
from tests.helpers import start_anonymous


async def test_items_are_served_in_english_with_honest_translation_status(
    client: AsyncClient,
) -> None:
    phq = (await client.get("/api/v1/assessments/PHQ9/items")).json()
    assert len(phq["items"]) == 9
    assert [o["value"] for o in phq["options"]] == [0, 1, 2, 3]
    assert phq["options"][0]["label"] == "Not at all"
    assert phq["difficulty_options"][3]["label"] == "Extremely difficult"
    assert phq["translation_available"] is True
    assert "No permission required" in phq["attribution"]

    tamil = (await client.get("/api/v1/assessments/GAD7/items", params={"locale": "ta"})).json()
    assert len(tamil["items"]) == 7
    assert tamil["item_locale"] == "en"
    assert tamil["requested_locale"] == "ta"
    assert tamil["translation_available"] is False


async def test_unknown_instrument_is_404_or_422(client: AsyncClient) -> None:
    response = await client.get("/api/v1/assessments/BDI/items")
    assert response.status_code == 422


async def test_submitting_requires_a_session(client: AsyncClient) -> None:
    response = await client.post("/api/v1/assessments/PHQ9", json={"answers": [0] * 9})
    assert response.status_code == 401


async def test_submit_scores_and_stores_the_result(client: AsyncClient) -> None:
    await start_anonymous(client)

    response = await client.post(
        "/api/v1/assessments/PHQ9",
        json={"answers": [1, 2, 1, 2, 1, 1, 1, 1, 0], "functional_difficulty": 1},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["total"] == 10
    assert body["max_score"] == 27
    assert body["severity_band"] == "moderate"
    assert body["next_step"] == "talk_to_someone"
    assert body["safety_item_positive"] is False
    assert body["functional_difficulty"] == 1


async def test_invalid_submissions_are_rejected(client: AsyncClient) -> None:
    await start_anonymous(client)
    for payload in (
        {"answers": [0] * 8},
        {"answers": [0] * 6 + [4]},
        {"answers": [0] * 6 + [-1]},
        {"answers": [0] * 7, "functional_difficulty": 4},
    ):
        instrument = "GAD7" if len(payload["answers"]) == 7 else "PHQ9"  # type: ignore[arg-type]
        response = await client.post(f"/api/v1/assessments/{instrument}", json=payload)
        assert response.status_code == 422, payload


async def test_item9_records_a_content_free_safety_event(app: FastAPI, client: AsyncClient) -> None:
    await start_anonymous(client)

    response = await client.post("/api/v1/assessments/PHQ9", json={"answers": [0] * 8 + [1]})

    assert response.json()["safety_item_positive"] is True
    resources: Resources = app.state.resources
    async with resources.sessionmaker() as session:
        events = (await session.scalars(select(SafetyEvent))).all()
    assert len(events) == 1
    event = events[0]
    assert (event.source, event.level, event.detector) == ("phq9_item9", "urgent", "questionnaire")
    assert event.resources_shown == ["tele_manas", "emergency_112"]
    columns = {c.key for c in inspect(SafetyEvent).columns}
    assert not columns & {"content", "message", "text", "answers", "note"}


async def test_no_safety_event_without_item9(app: FastAPI, client: AsyncClient) -> None:
    await start_anonymous(client)
    await client.post("/api/v1/assessments/PHQ9", json={"answers": [3] * 8 + [0]})
    await client.post("/api/v1/assessments/GAD7", json={"answers": [3] * 7})

    resources: Resources = app.state.resources
    async with resources.sessionmaker() as session:
        assert (await session.scalars(select(SafetyEvent))).all() == []


async def test_history_is_newest_first_filterable_and_private(
    app: FastAPI, client: AsyncClient
) -> None:
    await start_anonymous(client)
    await client.post("/api/v1/assessments/PHQ9", json={"answers": [0] * 9})
    await client.post("/api/v1/assessments/GAD7", json={"answers": [1] * 7})
    await client.post("/api/v1/assessments/PHQ9", json={"answers": [2] * 8 + [0]})

    history = (await client.get("/api/v1/assessments/history")).json()
    assert [(h["type"], h["total"]) for h in history] == [("PHQ9", 16), ("GAD7", 7), ("PHQ9", 0)]

    only_gad = (await client.get("/api/v1/assessments/history", params={"type": "GAD7"})).json()
    assert [h["total"] for h in only_gad] == [7]

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as other:
        await start_anonymous(other)
        assert (await other.get("/api/v1/assessments/history")).json() == []
