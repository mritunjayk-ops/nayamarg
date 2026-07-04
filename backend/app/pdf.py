from pathlib import Path
from textwrap import wrap
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.config import GENERATED_DIR


def _para(text: Any, style: ParagraphStyle) -> Paragraph:
    safe = str(text or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return Paragraph(safe, style)


def _bullets(items: list[Any], style: ParagraphStyle) -> ListFlowable:
    return ListFlowable([ListItem(_para(item, style)) for item in items], bulletType="bullet")


def export_blueprint_pdf(blueprint: dict[str, Any], candidate_id: int, tier: str) -> Path:
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    output = GENERATED_DIR / f"candidate_{candidate_id}_{tier}_blueprint.pdf"
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Small", parent=styles["BodyText"], fontSize=8, leading=10))
    styles.add(ParagraphStyle(name="Tight", parent=styles["BodyText"], fontSize=9, leading=12))
    styles.add(ParagraphStyle(name="Section", parent=styles["Heading2"], spaceBefore=12, spaceAfter=6))

    doc = SimpleDocTemplate(
        str(output),
        pagesize=A4,
        rightMargin=0.55 * inch,
        leftMargin=0.55 * inch,
        topMargin=0.55 * inch,
        bottomMargin=0.55 * inch,
    )

    story: list[Any] = []
    story.append(_para("Career Discovery & Transition Blueprint", styles["Title"]))
    story.append(_para(f"Candidate #{candidate_id} | Tier: {tier.title()}", styles["Tight"]))
    story.append(Spacer(1, 10))

    story.append(_para("Candidate Snapshot", styles["Section"]))
    snapshot = blueprint.get("snapshot", {})
    rows = [[_para(key.replace("_", " ").title(), styles["Small"]), _para(value, styles["Small"])] for key, value in snapshot.items()]
    table = Table(rows, colWidths=[1.7 * inch, 4.6 * inch])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F3F4F6")),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#D1D5DB")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(table)

    story.append(_para("Diagnosis", styles["Section"]))
    story.append(_para(blueprint.get("diagnosis", ""), styles["BodyText"]))

    story.append(_para("Transferable Strengths", styles["Section"]))
    story.append(_bullets(blueprint.get("strengths", []), styles["BodyText"]))

    story.append(_para("Recommended Career Paths", styles["Section"]))
    for i, path in enumerate(blueprint.get("paths", []), start=1):
        rank = path.get("rank", i)
        story.append(_para(f"{rank}. {path.get('title', 'Career path')} - Fit Score {path.get('score', '-')}/100", styles["Heading3"]))
        story.append(_para(path.get("why", ""), styles["BodyText"]))
        story.append(_bullets(path.get("proof_points", []), styles["BodyText"]))

    story.append(PageBreak())
    plan = blueprint.get("plan", {}) if isinstance(blueprint.get("plan"), dict) else {}
    days = plan.get("days", [])
    story.append(_para(f"Your Day-by-Day Plan ({plan.get('total_days', len(days))} days)", styles["Section"]))
    if plan.get("rationale"):
        story.append(_para(plan["rationale"], styles["Tight"]))
        story.append(Spacer(1, 6))
    for i, day in enumerate(days, start=1):
        story.append(_para(f"Day {day.get('day', i)}: {day.get('focus', '')}", styles["Heading3"]))
        if day.get("topics"):
            story.append(_bullets(day.get("topics", []), styles["BodyText"]))
        for course in day.get("courses", []) or []:
            label = " - ".join(x for x in [course.get("name"), course.get("provider")] if x)
            url = course.get("url", "")
            story.append(_para(f"Course: {label} {url}".strip(), styles["Tight"]))
        if day.get("task"):
            story.append(_para(f"Task: {day['task']}", styles["Tight"]))

    story.append(PageBreak())
    story.append(_para("Projects", styles["Section"]))
    for project in blueprint.get("projects", []):
        story.append(_para(project.get("name", "Project"), styles["Heading3"]))
        story.append(_para(project.get("description", ""), styles["BodyText"]))
        story.append(_bullets(project.get("skills", []), styles["BodyText"]))

    story.append(_para("Resume Positioning", styles["Section"]))
    story.append(_bullets(blueprint.get("resume_bullets", []), styles["BodyText"]))

    story.append(_para("Market Signals Used", styles["Section"]))
    market_items = []
    for item in blueprint.get("market_signals", []):
        source = item.get("source", "Market source")
        title = item.get("title", "")
        market_items.append(f"{source}: {title}")
    story.append(_bullets(market_items or ["No live market search was available; fallback skill demand assumptions were used."], styles["BodyText"]))

    story.append(_para("Important Note", styles["Section"]))
    story.append(
        _para(
            "This report is decision support, not a guarantee of admission, employment, or income. Use it with human judgment and update it as market data changes.",
            styles["Small"],
        )
    )

    doc.build(story)
    return output
