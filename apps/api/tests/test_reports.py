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


async def test_reports_need_a_session(client: AsyncClient) -> None:
    assert (await client.get("/api/v1/reports/screening.pdf")).status_code == 401
