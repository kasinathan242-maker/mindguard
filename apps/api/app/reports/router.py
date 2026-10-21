"""Screening summary: the same content as JSON (web view) and as a PDF to share with a professional.

Three kinds of information are kept visibly separate:
- validated questionnaire scores (PHQ-9, GAD-7),
- self-reported check-ins (the person's own ratings),
- a diagnosis, which MindGuard never provides.
No risk percentage appears anywhere.
"""

import io
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy import select

from app.assessments.instruments import get_instrument
from app.assessments.models import Assessment
from app.auth.models import User
from app.checkins.models import Checkin
from app.consent.deps import require_consent
from app.core.deps import SessionDep
from app.db.types import utcnow
from app.integrations.wearables import WearableSample
from app.reports.patterns import Pattern, daily_mean, mood_patterns
from app.safety.resources import localised_resources

router = APIRouter(tags=["reports"])
CoreUser = Annotated[User, Depends(require_consent("core"))]

BAND_LABELS = {
    "minimal": "Minimal",
    "mild": "Mild",
    "moderate": "Moderate",
    "moderately_severe": "Moderately severe",
    "severe": "Severe",
}
NEXT_STEPS = {
    "self_care": "Keep looking after yourself and check in again in two weeks.",
    "talk_to_someone": "Consider talking with a counsellor or someone you trust.",
    "consult_professional": "Please consider seeing a doctor, psychologist or counsellor soon.",
}
DISCLAIMER = (
    "This is a screening summary, not a diagnosis. Questionnaire scores describe how the person "
    "has been feeling over the last two weeks. MindGuard AI does not diagnose any condition."
)


class ScoreOut(BaseModel):
    type: str
    name: str
    total: int
    max_score: int
    band: str
    date: datetime


class TrendPoint(BaseModel):
    type: str
    total: int
    date: datetime


class MoodSummary(BaseModel):
    days: int
    checkins: int
    average_mood: float | None
    average_energy: float | None
    average_sleep_hours: float | None


class Summary(BaseModel):
    generated_at: datetime
    latest: list[ScoreOut]
    trend: list[TrendPoint]
    mood: MoodSummary
    next_step: str | None
    patterns: list[Pattern]
    resources: list[str]
    disclaimer: str


async def build_summary(session: SessionDep, user: User, days: int = 30) -> Summary:
    rows = (
        await session.scalars(
            select(Assessment).where(Assessment.user_id == user.id).order_by(Assessment.created_at)
        )
    ).all()
    latest: dict[str, Assessment] = {}
    for row in rows:
        latest[row.type] = row
    scores = [
        ScoreOut(
            type=row.type,
            name=get_instrument(row.type).title,
            total=row.total,
            max_score=get_instrument(row.type).max_score,
            band=row.severity_band,
            date=row.created_at,
        )
        for row in latest.values()
    ]
    worst_step = None
    order = ["self_care", "talk_to_someone", "consult_professional"]
    for row in latest.values():
        band = get_instrument(row.type).band_for(row.total)
        step = "consult_professional" if row.safety_item_positive else band.next_step
        if worst_step is None or order.index(step) > order.index(worst_step):
            worst_step = step

    since = utcnow().timestamp() - days * 86_400
    checkins = [
        c
        for c in (await session.scalars(select(Checkin).where(Checkin.user_id == user.id))).all()
        if c.created_at.timestamp() >= since
    ]
    sleeps = [c.sleep_hours for c in checkins if c.sleep_hours is not None]

    def mean(values: list[float]) -> float | None:
        return round(sum(values) / len(values), 1) if values else None

    return Summary(
        generated_at=utcnow(),
        latest=scores,
        trend=[TrendPoint(type=r.type, total=r.total, date=r.created_at) for r in rows],
        mood=MoodSummary(
            days=days,
            checkins=len(checkins),
            average_mood=mean([float(c.mood) for c in checkins]),
            average_energy=mean([float(c.energy) for c in checkins]),
            average_sleep_hours=mean(sleeps),
        ),
        next_step=NEXT_STEPS[worst_step] if worst_step else None,
        patterns=await _patterns(session, user),
        resources=[f"{r.name}: {r.display_number}" for r in localised_resources("en")],
        disclaimer=DISCLAIMER,
    )


async def _patterns(session: SessionDep, user: User) -> list[Pattern]:
    """Uses up to 90 days. Sleep comes from check-ins and imported wearable data."""
    checkins = (await session.scalars(select(Checkin).where(Checkin.user_id == user.id))).all()
    mood = daily_mean([(c.created_at.date(), float(c.mood)) for c in checkins])
    sleep = daily_mean(
        [(c.created_at.date(), float(c.sleep_hours)) for c in checkins if c.sleep_hours is not None]
    )
    samples = (
        await session.scalars(select(WearableSample).where(WearableSample.user_id == user.id))
    ).all()
    for s in samples:
        if s.metric == "sleep_minutes" and s.day not in sleep:
            sleep[s.day] = s.value / 60
    steps = {s.day: s.value for s in samples if s.metric == "steps"}
    return mood_patterns(mood, {"sleep_hours": sleep, "steps": steps})


@router.get("/insights/summary")
async def summary(user: CoreUser, session: SessionDep) -> Summary:
    return await build_summary(session, user)


def render_pdf(data: Summary) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, title="Screening summary"
    )
    styles = getSampleStyleSheet()
    story: list[object] = [
        Paragraph("MindGuard AI: screening summary", styles["Title"]),
        Paragraph(f"Generated {data.generated_at:%d %b %Y}", styles["Normal"]),
        Spacer(1, 6 * mm),
        Paragraph(DISCLAIMER, styles["Italic"]),
        Spacer(1, 6 * mm),
        Paragraph("1. Questionnaire scores (validated instruments)", styles["Heading2"]),
    ]
    if data.latest:
        table = Table(
            [["Questionnaire", "Score", "Range", "Date"]]
            + [
                [
                    s.name,
                    f"{s.total} / {s.max_score}",
                    BAND_LABELS.get(s.band, s.band),
                    f"{s.date:%d %b %Y}",
                ]
                for s in data.latest
            ],
            hAlign="LEFT",
        )
        table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.grey),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        story.append(table)
        history = ", ".join(f"{p.type} {p.total} ({p.date:%d %b})" for p in data.trend)
        story += [Spacer(1, 3 * mm), Paragraph(f"Score history: {history}", styles["Normal"])]
    else:
        story.append(Paragraph("No questionnaires completed yet.", styles["Normal"]))

    m = data.mood
    story += [
        Spacer(1, 5 * mm),
        Paragraph(f"2. Self-reported check-ins (last {m.days} days)", styles["Heading2"]),
        Paragraph(
            f"{m.checkins} check-ins. Average mood {m.average_mood or '-'} / 5, average energy "
            f"{m.average_energy or '-'} / 5, average sleep {m.average_sleep_hours or '-'} hours. "
            "These are the person's own ratings, not a clinical measure.",
            styles["Normal"],
        ),
        Spacer(1, 5 * mm),
        Paragraph("3. Diagnosis", styles["Heading2"]),
        Paragraph("Not provided. MindGuard AI is a screening and support tool.", styles["Normal"]),
        Spacer(1, 5 * mm),
        Paragraph("Suggested next step", styles["Heading2"]),
        Paragraph(data.next_step or "Complete a self-check to get a suggestion.", styles["Normal"]),
        Spacer(1, 5 * mm),
        Paragraph("Free support in India", styles["Heading2"]),
        *[Paragraph(r, styles["Normal"]) for r in data.resources],
    ]
    doc.build(story)
    return buffer.getvalue()


@router.get("/reports/screening.pdf")
async def screening_pdf(user: CoreUser, session: SessionDep) -> Response:
    pdf = render_pdf(await build_summary(session, user))
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="mindguard-screening-summary.pdf"'},
    )
