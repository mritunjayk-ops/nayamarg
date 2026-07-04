"""Blueprint engine.

Agentic in the way that matters: the model plans its own research per candidate,
we run those live web searches (Tavily) to find real courses and market signals,
and the model synthesizes a genuinely personalized blueprint — biased toward
tech/data/AI where the background fits — with a variable-length, day-by-day plan.

Flow:  normalize → research (plan queries → Tavily) → synthesize → export_pdf

Control flow is deterministic (reliable, no runaway loops); the *content* is
model-driven and evidence-grounded. If no model provider is available, a small
deterministic fallback keeps the app working.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from langgraph.graph import END, StateGraph

from app.config import get_settings
from app.model_gateway import complete_json
from app.models import AgentState
from app.pdf import export_blueprint_pdf

logger = logging.getLogger("nayamarg.agent")

MAX_EVIDENCE = 24
EVIDENCE_CHARS = 6000  # cap evidence sent to the synthesis prompt


# ---------------------------------------------------------------- normalize
def normalize_profile(state: AgentState) -> AgentState:
    c = state["candidate"]
    split = lambda s: [x.strip() for x in str(s or "").replace(",", ";").split(";") if x.strip()]
    return {
        "normalized": {
            "age_group": c.get("age_group", ""),
            "qualification": c.get("qualification", ""),
            "background": c.get("background", ""),
            "exams": c.get("exams", ""),
            "years_preparing": c.get("years_preparing", ""),
            "current_situation": c.get("current_situation", ""),
            "main_stress": c.get("main_stress", ""),
            "worries": split(c.get("worries", "")),
            "interests": split(c.get("interests", "")),
            "story": c.get("situation_words", ""),
        }
    }


# ---------------------------------------------------------------- research
def research(state: AgentState) -> AgentState:
    queries = _plan_queries(state["normalized"])
    evidence = _tavily_search(queries)
    logger.info("research: %d queries, %d evidence items", len(queries), len(evidence))
    return {"queries": queries, "evidence": evidence}


def _plan_queries(profile: dict[str, Any]) -> list[str]:
    prompt = f"""You are planning live web research to build a career-transition plan for an Indian competitive-exam aspirant moving into a new career. Bias toward tech / data / AI roles where the background genuinely supports it, but stay realistic.

Candidate:
{json.dumps(profile, ensure_ascii=False, indent=2)}

Write 5 focused web-search queries that will surface: (1) realistic roles that fit this background, (2) in-demand skills for those roles in India in 2026, (3) specific well-rated online courses (Udemy, Coursera, etc.) for those skills, (4) how someone with this background breaks in, (5) current hiring/demand signals.

Return ONLY JSON: {{"queries": ["q1","q2","q3","q4","q5"]}}"""
    result = complete_json(prompt, task="research", temperature=0.3, max_tokens=500)
    if result and isinstance(result.get("queries"), list) and result["queries"]:
        return [str(q) for q in result["queries"] if str(q).strip()][:6]

    bg = profile.get("background") or "graduate"
    return [
        f"best entry-level data and AI roles in India 2026 for a {bg}",
        "most in-demand data and AI skills India 2026",
        "top rated Udemy Coursera courses data analytics python SQL 2026",
        f"how to transition from {bg} into a data or AI career India",
        "entry level AI data analyst hiring demand India 2026",
    ]


def _tavily_search(queries: list[str]) -> list[dict[str, str]]:
    settings = get_settings()
    if not settings.tavily_api_key:
        return []
    evidence: list[dict[str, str]] = []
    try:
        from tavily import TavilyClient

        client = TavilyClient(api_key=settings.tavily_api_key)
        for q in queries:
            try:
                res = client.search(query=q, max_results=4, search_depth="basic")
            except Exception as exc:  # one query failing shouldn't sink the rest
                logger.warning("tavily query failed (%s): %s", q, exc)
                continue
            for item in res.get("results", []):
                evidence.append(
                    {
                        "query": q,
                        "title": item.get("title", ""),
                        "url": item.get("url", ""),
                        "content": (item.get("content", "") or "")[:600],
                    }
                )
    except Exception as exc:
        logger.warning("tavily unavailable: %s", exc)
    return evidence[:MAX_EVIDENCE]


# ---------------------------------------------------------------- synthesize
def synthesize(state: AgentState) -> AgentState:
    profile = state["normalized"]
    tier = state.get("tier", "mini")
    language = state.get("language", "english")
    sample = tier == "sample"
    path_count = 2 if sample else 3

    prompt = _synthesis_prompt(profile, state.get("evidence", []), path_count, sample, language)
    parsed = complete_json(prompt, task="blueprint", temperature=0.4, max_tokens=8000)

    blueprint = _normalize_blueprint(parsed, profile, path_count) if parsed else _fallback_blueprint(profile, path_count, sample)
    return {"blueprint": blueprint, "summary": _summary(blueprint, tier)}


def _synthesis_prompt(profile: dict[str, Any], evidence: list[dict[str, str]], path_count: int, sample: bool, language: str) -> str:
    scope = (
        "This is a FREE SAMPLE: include only the first 1-2 modules of the curriculum as a preview."
        if sample
        else "Include the COMPLETE curriculum: every module and topic needed to become genuinely job-ready."
    )
    return f"""You are a senior career-transition advisor for Indian UPSC / competitive-exam aspirants moving into new careers. Write in {language}. Be specific, honest, empathetic, and evidence-grounded. No generic motivation. Reframe their exam years as real transferable capability — never hide the gap, reposition it.

Bias recommendations toward tech / data / AI roles where the background genuinely supports it, but stay realistic — do not force a tech path onto someone it does not fit.

CANDIDATE:
{json.dumps(profile, ensure_ascii=False, indent=2)}

LIVE RESEARCH EVIDENCE (use for REAL course names/providers/URLs and current market signals; cite URLs you actually use; never invent URLs):
{json.dumps(evidence, ensure_ascii=False)[:EVIDENCE_CHARS]}

Produce exactly {path_count} career paths, ranked, each scored 0-100 for fit. Then build a realistic LEARNING PLAN for the TOP path.

BE HONEST ABOUT TIME — this is critical. Real, job-ready skill takes MONTHS, not weeks. As a rough benchmark at about 2 hours of focused study per day: core data analysis ~2 months, machine learning ~1 further month, AI / deep learning ~2 further months. Do NOT compress timelines or promise fast results. Overall duration should realistically land around 3-6 months for a full tech/data transition.

For the learning plan:
- Recommend only 2-3 courses TOTAL (people cannot start a new course every day). Prefer real courses named in the evidence.
- Break the learning into MODULES, and within each module list TOPICS drawn from those 2-3 courses.
- For EACH topic give: what to learn, which recommended course covers it, and a realistic time estimate phrased like "~2 days at 2 hrs/day" or "~6 hours".
- Give an overall estimated_duration as a FLEXIBLE range (e.g. "3-4 months") and state the pace assumption. Do NOT enumerate day numbers — progress is tracked by topic completion, not by day.
{scope}

Return ONLY valid JSON with EXACTLY this schema:
{{
  "snapshot": {{"age_group":"","qualification":"","background":"","exam_history":"","current_situation":"","main_stress":"","interests":""}},
  "diagnosis": "150-220 word honest, specific read of where they stand and the way forward",
  "strengths": ["8-12 concrete transferable strengths"],
  "paths": [{{"rank":1,"title":"","score":0,"why":"specific fit rationale grounded in their background and the market","proof_points":["","",""]}}],
  "learning": {{
    "estimated_duration": "flexible range, e.g. 3-4 months",
    "pace_assumption": "e.g. assuming about 2 hours of focused study per day",
    "courses": [{{"name":"","provider":"","url":""}}],
    "modules": [{{"title":"","topics":[{{"topic":"","details":"what to learn","course":"which recommended course covers it","estimate":"~2 days at 2 hrs/day"}}]}}]
  }},
  "projects": [{{"name":"","description":"","skills":["",""]}}],
  "resume_bullets": ["4-6 truthful resume bullets reframing exam prep plus new skills"],
  "market_signals": [{{"source":"","title":"","url":""}}]
}}

Rules:
- Exactly {path_count} paths.
- Only 2-3 courses total; every topic's "course" must be one of them.
- Time estimates must be realistic (the total spans months), each phrased with a study-pace assumption.
- Courses must be real — prefer ones named in the evidence; never invent fake URLs.
- Do not mention being an AI model."""


def _normalize_blueprint(bp: dict[str, Any], profile: dict[str, Any], path_count: int) -> dict[str, Any]:
    if not isinstance(bp, dict):
        return _fallback_blueprint(profile, path_count, sample=False)

    snap = bp.get("snapshot") if isinstance(bp.get("snapshot"), dict) else {}
    defaults = {
        "age_group": profile.get("age_group", ""),
        "qualification": profile.get("qualification", ""),
        "background": profile.get("background", ""),
        "exam_history": profile.get("exams", ""),
        "current_situation": profile.get("current_situation", ""),
        "main_stress": profile.get("main_stress", ""),
        "interests": "; ".join(profile.get("interests", [])),
    }
    bp["snapshot"] = {k: (snap.get(k) or v) for k, v in defaults.items()}

    bp["diagnosis"] = bp.get("diagnosis") or ""
    bp["strengths"] = [s for s in bp.get("strengths", []) if s] if isinstance(bp.get("strengths"), list) else []
    bp["paths"] = [p for p in bp.get("paths", []) if isinstance(p, dict)][:path_count] if isinstance(bp.get("paths"), list) else []

    learning = bp.get("learning") if isinstance(bp.get("learning"), dict) else {}
    learning["estimated_duration"] = learning.get("estimated_duration") or ""
    learning["pace_assumption"] = learning.get("pace_assumption") or ""
    learning["courses"] = [c for c in learning.get("courses", []) if isinstance(c, dict)][:4] if isinstance(learning.get("courses"), list) else []
    modules = [m for m in learning.get("modules", []) if isinstance(m, dict)] if isinstance(learning.get("modules"), list) else []
    for m in modules:
        m["title"] = m.get("title") or ""
        m["topics"] = [t for t in m.get("topics", []) if isinstance(t, dict)] if isinstance(m.get("topics"), list) else []
    learning["modules"] = modules
    bp["learning"] = learning

    bp["projects"] = [p for p in bp.get("projects", []) if isinstance(p, dict)] if isinstance(bp.get("projects"), list) else []
    bp["resume_bullets"] = [b for b in bp.get("resume_bullets", []) if b] if isinstance(bp.get("resume_bullets"), list) else []
    bp["market_signals"] = [m for m in bp.get("market_signals", []) if isinstance(m, dict)] if isinstance(bp.get("market_signals"), list) else []
    return bp


def _summary(bp: dict[str, Any], tier: str) -> str:
    paths = bp.get("paths", [])
    top = paths[0].get("title", "your next path") if paths else "your next path"
    learning = bp.get("learning", {})
    topics = sum(len(m.get("topics", [])) for m in learning.get("modules", []))
    duration = learning.get("estimated_duration") or "a few months"
    kind = "sample" if tier == "sample" else "full"
    return f"Your {kind} blueprint: {len(paths)} fitted path(s) led by {top}, with a {topics}-topic plan spanning about {duration}."


def _fallback_blueprint(profile: dict[str, Any], path_count: int, sample: bool) -> dict[str, Any]:
    # ponytail: last-resort only — fires only when BOTH OpenAI and Groq are unavailable.
    logger.warning("synthesis unavailable — using deterministic fallback blueprint")
    paths = [
        {"rank": 1, "title": "Data Analyst", "score": 82, "why": "Converts your research, synthesis, and quantitative discipline into a fast, portfolio-provable path.", "proof_points": ["Provable via a small dashboard portfolio", "Exam gap reframes cleanly as structured self-study", "Strong entry-level demand in India"]},
        {"rank": 2, "title": "AI Product / Operations Analyst", "score": 78, "why": "Uses your writing, documentation, and process discipline in fast-growing AI-adjacent roles.", "proof_points": ["Low coding barrier to start", "Values written clarity you already have", "Growing at startups and services firms"]},
        {"rank": 3, "title": "Junior AI / Software Builder", "score": 74, "why": "If you enjoy building, exam-grade discipline transfers well to learning to code.", "proof_points": ["GitHub portfolio proves skill directly", "Clear self-study path", "High ceiling"]},
    ][:path_count]
    modules = [
        {"title": "Foundations", "topics": [
            {"topic": "Spreadsheets & data cleaning", "details": "pivots, lookups, cleaning messy data", "course": "Google Data Analytics (Coursera)", "estimate": "~4 days at 2 hrs/day"},
            {"topic": "SQL basics", "details": "SELECT, JOIN, GROUP BY, aggregations", "course": "Google Data Analytics (Coursera)", "estimate": "~5 days at 2 hrs/day"},
        ]},
        {"title": "Core analysis", "topics": [
            {"topic": "Python for data (pandas)", "details": "dataframes, cleaning, aggregation", "course": "Google Data Analytics (Coursera)", "estimate": "~2 weeks at 2 hrs/day"},
            {"topic": "Visualization & dashboards", "details": "charts, Tableau or Power BI basics", "course": "Google Data Analytics (Coursera)", "estimate": "~1 week at 2 hrs/day"},
        ]},
    ]
    if sample:
        modules = modules[:1]
    learning = {
        "estimated_duration": "3-4 months",
        "pace_assumption": "assuming about 2 hours of focused study per day",
        "courses": [{"name": "Google Data Analytics Professional Certificate", "provider": "Coursera", "url": "https://www.coursera.org/professional-certificates/google-data-analytics"}],
        "modules": modules,
    }
    return {
        "snapshot": {
            "age_group": profile.get("age_group", ""),
            "qualification": profile.get("qualification", ""),
            "background": profile.get("background", ""),
            "exam_history": profile.get("exams", ""),
            "current_situation": profile.get("current_situation", ""),
            "main_stress": profile.get("main_stress", ""),
            "interests": "; ".join(profile.get("interests", [])),
        },
        "diagnosis": "We could not reach the AI service to generate a fully personalized read just now. This is a safe fallback plan; regenerate for a tailored version.",
        "strengths": ["Structured self-study", "Analytical writing", "Research synthesis", "Discipline under pressure", "Current-affairs awareness", "Quantitative reasoning"],
        "paths": paths,
        "learning": learning,
        "projects": [{"name": "Portfolio starter project", "description": "A small, visible project that proves one job-relevant skill.", "skills": ["analysis", "communication"]}],
        "resume_bullets": ["Reframed competitive-exam preparation as structured research and analytical writing.", "Building portfolio projects to prove job-relevant skills."],
        "market_signals": [],
    }


# ---------------------------------------------------------------- export
def export_pdf(state: AgentState) -> AgentState:
    candidate_id = int(state["candidate"].get("id", 0))
    tier = state.get("tier", "mini")
    path = export_blueprint_pdf(state["blueprint"], candidate_id, tier)
    return {"pdf_path": str(path)}


# ---------------------------------------------------------------- graph
def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("normalize_profile", normalize_profile)
    graph.add_node("research", research)
    graph.add_node("synthesize", synthesize)
    graph.add_node("export_pdf", export_pdf)

    graph.set_entry_point("normalize_profile")
    graph.add_edge("normalize_profile", "research")
    graph.add_edge("research", "synthesize")
    graph.add_edge("synthesize", "export_pdf")
    graph.add_edge("export_pdf", END)
    return graph.compile()


career_graph = build_graph()


def run_blueprint(candidate: dict[str, Any], tier: str, language: str = "english") -> AgentState:
    return career_graph.invoke({"candidate": candidate, "tier": tier, "language": language})
