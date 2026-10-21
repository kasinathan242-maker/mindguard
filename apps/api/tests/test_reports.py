from httpx import AsyncClient

from tests.helpers import start_anonymous


async def test_summary_separates_scores_self_report_and_diagnosis(client: AsyncClient) -> None:
    await start_anonymous(client)
    await client.post("/api/v1/assessments/PHQ9", json={"answers": [1, 2, 1, 2, 1, 1, 1, 1, 0]})
    await client.post("/api/v1/assessments/GAD7", json={"answers": [0] * 7})
    await client.post("/api/v1/checkins", json={"mood": 2, "energy": 4, "sleep_hours": 6})

    data = (await client.get("/api/v1/insights/summary")).json()

    assert {s["type"]: s["band"] for s in data["latest"]} == {"PHQ9": "moderate", "GAD7": "minimal"}
    assert data["mood"]["checkins"] == 1
    assert data["mood"]["average_mood"] == 2.0
    assert data["next_step"].startswith("Consider talking")
    assert "not a diagnosis" in data["disclaimer"]
    assert "%" not in str(data)


async def test_pdf_download(client: AsyncClient) -> None:
    await start_anonymous(client)
    await client.post("/api/v1/assessments/GAD7", json={"answers": [2] * 7})

    response = await client.get("/api/v1/reports/screening.pdf")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")
    assert "attachment" in response.headers["content-disposition"]


async def test_pdf_download_tamil(client: AsyncClient) -> None:
    await start_anonymous(client)
    await client.post("/api/v1/assessments/PHQ9", json={"answers": [1, 2, 1, 2, 1, 1, 1, 1, 0]})
    await client.post("/api/v1/checkins", json={"mood": 3, "energy": 3, "sleep_hours": 7})

    response = await client.get("/api/v1/reports/screening.pdf?locale=ta")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")
    assert "mindguard-screening-summary-ta.pdf" in response.headers["content-disposition"]


async def test_summary_tamil(client: AsyncClient) -> None:
    await start_anonymous(client)
    await client.post("/api/v1/assessments/PHQ9", json={"answers": [1, 2, 1, 2, 1, 1, 1, 1, 0]})

    data = (await client.get("/api/v1/insights/summary?locale=ta")).json()
    assert "பேசுங்கள்" in data["next_step"] or "ஆலோசகர்" in data["next_step"]
    assert "சுய மதிப்பீட்டு சுருக்கம்" in data["disclaimer"]


async def test_reports_need_a_session(client: AsyncClient) -> None:
    assert (await client.get("/api/v1/reports/screening.pdf")).status_code == 401


def test_patterns_hidden_below_14_days_and_signed_correctly() -> None:
    from datetime import date, timedelta

    from app.reports.patterns import mood_patterns

    days = [date(2026, 9, 1) + timedelta(days=i) for i in range(20)]
    mood = {d: float(1 + i % 5) for i, d in enumerate(days)}
    sleep = {d: 4.0 + (i % 5) for i, d in enumerate(days)}  # rises with mood
    few = dict.fromkeys(days[:10], 5.0)
    patterns = {p.metric: p for p in mood_patterns(mood, {"sleep_hours": sleep, "steps": few})}
    assert patterns["sleep_hours"].correlation == 1.0
    assert patterns["sleep_hours"].strength == "strong"
    assert patterns["steps"].correlation is None
    assert patterns["steps"].strength == "not enough data"


async def test_summary_includes_patterns(client: AsyncClient) -> None:
    await start_anonymous(client)
    data = (await client.get("/api/v1/insights/summary")).json()
    assert {p["metric"] for p in data["patterns"]} == {"sleep_hours", "steps"}
    assert all(p["strength"] == "not enough data" for p in data["patterns"])
