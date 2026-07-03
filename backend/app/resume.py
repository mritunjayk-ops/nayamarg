from __future__ import annotations

from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import ListFlowable, ListItem, Paragraph, SimpleDocTemplate, Spacer

from app.config import GENERATED_DIR
from app.model_gateway import complete_json
from app.models import CandidateIntake, JobItem, ResumeDocument, ResumeProject


def generate_resume(candidate: CandidateIntake, target_role: str, job: JobItem | None = None) -> ResumeDocument:
    ai_resume = _try_ai_resume(candidate, target_role, job)
    if ai_resume:
        return ai_resume
    return _fallback_resume(candidate, target_role, job)


def export_resume_pdf(resume: ResumeDocument, filename: str = "resume.pdf") -> Path:
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    path = GENERATED_DIR / filename
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="ResumeName", parent=styles["Title"], fontSize=18, leading=22, spaceAfter=6))
    styles.add(ParagraphStyle(name="ResumeSection", parent=styles["Heading2"], fontSize=11, leading=14, textColor=colors.HexColor("#115E59"), spaceBefore=10, spaceAfter=4))
    styles.add(ParagraphStyle(name="ResumeBody", parent=styles["BodyText"], fontSize=9, leading=12))

    story: list[Any] = []
    story.append(_p(resume.headline, styles["ResumeName"]))
    story.append(_p(resume.summary, styles["ResumeBody"]))

    story.append(_p("Core Skills", styles["ResumeSection"]))
    story.append(_p(", ".join(resume.skills), styles["ResumeBody"]))

    story.append(_p("Projects", styles["ResumeSection"]))
    for project in resume.projects:
        story.append(_p(project.name, styles["Heading3"]))
        story.append(_p(project.description, styles["ResumeBody"]))
        story.append(_bullets(project.bullets, styles["ResumeBody"]))
        story.append(_p(f"Skills: {', '.join(project.skills)}", styles["ResumeBody"]))

    story.append(_p("Education", styles["ResumeSection"]))
    story.append(_bullets(resume.education, styles["ResumeBody"]))

    story.append(_p("Relevant Experience & Transition Positioning", styles["ResumeSection"]))
    story.append(_bullets(resume.experience, styles["ResumeBody"]))
    story.append(Spacer(1, 4))
    story.append(_p(resume.gap_positioning, styles["ResumeBody"]))

    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        rightMargin=0.55 * inch,
        leftMargin=0.55 * inch,
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch,
    )
    doc.build(story)
    return path


def _try_ai_resume(candidate: CandidateIntake, target_role: str, job: JobItem | None) -> ResumeDocument | None:
    parsed = complete_json(_resume_prompt(candidate, target_role, job), task="resume", temperature=0.25)
    if parsed is None:
        return None
    try:
        return ResumeDocument.model_validate(parsed)
    except Exception:
        return None


def _resume_prompt(candidate: CandidateIntake, target_role: str, job: JobItem | None) -> str:
    return f"""
Create a truthful ATS-friendly resume JSON for an Indian UPSC/competitive-exam aspirant transitioning to {target_role}.

Candidate:
{candidate.model_dump_json(indent=2)}

Target job:
{job.model_dump_json(indent=2) if job else "No specific job selected."}

Rules:
- Do not invent employment, degrees, companies, or credentials.
- Reframe exam preparation as structured self-study, research, analysis, and writing.
- Include project ideas as projects only if phrased as portfolio projects to build or built during transition.
- Keep language professional and concise.
- Return only valid JSON matching this schema:
{{
  "headline": "Name Placeholder | Target Role",
  "summary": "3-4 line professional summary",
  "skills": ["skill"],
  "projects": [
    {{
      "name": "Project name",
      "description": "One sentence",
      "bullets": ["achievement/action bullet"],
      "skills": ["skill"]
    }}
  ],
  "education": ["degree/background line"],
  "experience": ["truthful transition experience bullet"],
  "gap_positioning": "1-2 sentence gap explanation"
}}
"""


def _fallback_resume(candidate: CandidateIntake, target_role: str, job: JobItem | None) -> ResumeDocument:
    target = target_role or (job.title if job else "Data Analyst")
    skill_pool = [
        "Research synthesis",
        "Analytical writing",
        "Excel",
        "SQL fundamentals",
        "Python fundamentals",
        "Dashboarding",
        "Policy and current-affairs analysis",
        "Structured self-learning",
        "Stakeholder communication",
    ]
    interests = candidate.interests.lower()
    if "ai" in interests:
        skill_pool.extend(["LLM prompting", "AI workflow automation"])
    if "product" in interests:
        skill_pool.extend(["Product operations", "Requirement documentation"])
    if "policy" in interests:
        skill_pool.extend(["Policy memo writing", "Public dataset analysis"])

    project_title = "UPSC Preparation to Employability Analytics Dashboard"
    if job:
        project_title = f"{job.title} Readiness Portfolio Project"

    return ResumeDocument(
        headline=f"Candidate Name | {target}",
        summary=(
            f"Career-transition candidate with {candidate.background or 'academic'} background and competitive-exam preparation experience. "
            "Strong in structured research, self-learning, written synthesis, and disciplined execution. "
            f"Now building market-ready proof for {target} roles through focused projects and role-specific skills."
        ),
        skills=list(dict.fromkeys(skill_pool))[:14],
        projects=[
            ResumeProject(
                name=project_title,
                description="Portfolio project designed to convert exam-preparation discipline into visible job-relevant proof.",
                bullets=[
                    "Built a structured dataset from preparation milestones, mock performance, and skill gaps to identify transition priorities.",
                    "Created a dashboard and written insight brief to demonstrate analysis, communication, and decision support.",
                    "Mapped target job descriptions to missing skills and generated a weekly learning plan.",
                ],
                skills=["Excel", "Analytics", "Research", "Dashboarding", "Communication"],
            ),
            ResumeProject(
                name="AI-Assisted Job Market Research Tracker",
                description="A lightweight workflow for comparing job descriptions, extracting skills, and ranking fit.",
                bullets=[
                    "Collected remote job descriptions and extracted repeated skill requirements across target roles.",
                    "Scored jobs by current fit, missing skills, and application readiness.",
                    "Prepared tailored resume keywords and cover-letter talking points for shortlisted roles.",
                ],
                skills=["AI prompting", "Job research", "Data analysis", "Resume targeting"],
            ),
        ],
        education=[candidate.background or candidate.qualification or "Education details to be added"],
        experience=[
            f"Prepared for {candidate.exams or 'competitive examinations'} through a structured self-study program covering research, analysis, writing, and current affairs.",
            "Produced high-volume notes, revised complex subjects, and practiced time-bound problem solving under competitive constraints.",
            "Converted exam preparation into a focused career transition plan with portfolio projects and job-specific learning goals.",
        ],
        gap_positioning=(
            "The career gap is positioned as a deliberate competitive-exam preparation phase that built discipline, research ability, "
            "and analytical communication. The resume should pair this explanation with current portfolio projects to prove market readiness."
        ),
    )


def _p(text: str, style: ParagraphStyle) -> Paragraph:
    safe = str(text or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return Paragraph(safe, style)


def _bullets(items: list[str], style: ParagraphStyle) -> ListFlowable:
    return ListFlowable([ListItem(_p(item, style)) for item in items], bulletType="bullet")
