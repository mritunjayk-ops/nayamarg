from __future__ import annotations

import json
from typing import Any

from langgraph.graph import END, StateGraph

from app.config import get_settings
from app.model_gateway import complete_json
from app.models import AgentState
from app.pdf import export_blueprint_pdf


BASE_COURSES = {
    "Data Analyst": [
        "Excel for analysis: pivots, lookup formulas, dashboards",
        "SQL: SELECT, JOIN, GROUP BY, CTEs, window functions",
        "Python: pandas, numpy, matplotlib/seaborn",
        "Statistics: distributions, hypothesis testing, regression basics",
        "BI: Power BI or Tableau dashboarding",
    ],
    "AI Product / Operations Analyst": [
        "AI fundamentals: LLMs, embeddings, prompting, evaluation",
        "No-code/low-code automation with Zapier or Make",
        "Product analytics: funnels, retention, activation metrics",
        "Documentation: PRDs, SOPs, process maps",
        "Workflow automation using APIs and spreadsheets",
    ],
    "Policy / Research Analyst": [
        "Policy memo writing and evidence synthesis",
        "Public datasets: RBI, World Bank, MOSPI, NFHS, data.gov.in",
        "Research methods: source quality, citations, literature review",
        "Excel/Sheets analysis and visualization",
        "Briefing note and stakeholder presentation writing",
    ],
    "Software / AI Builder": [
        "Python programming fundamentals",
        "Web basics: HTML, CSS, JavaScript, APIs",
        "Backend basics: FastAPI, databases, auth",
        "AI app building: RAG, tool calling, agents",
        "GitHub portfolio and deployment",
    ],
}


def normalize_profile(state: AgentState) -> AgentState:
    candidate = state["candidate"]
    interests = [item.strip() for item in candidate.get("interests", "").split(";") if item.strip()]
    worries = [item.strip() for item in candidate.get("worries", "").split(";") if item.strip()]
    normalized = {
        "age_group": candidate.get("age_group", ""),
        "qualification": candidate.get("qualification", ""),
        "background": candidate.get("background", ""),
        "exams": candidate.get("exams", ""),
        "years_preparing": candidate.get("years_preparing", ""),
        "current_situation": candidate.get("current_situation", ""),
        "main_stress": candidate.get("main_stress", ""),
        "worries": worries,
        "interests": interests,
        "story": candidate.get("situation_words", ""),
        "trust_factor": candidate.get("trust_factor", ""),
        "price_preference": candidate.get("price_preference", ""),
    }
    return {"normalized": normalized}


def diagnose_candidate(state: AgentState) -> AgentState:
    profile = state["normalized"]
    background = profile["background"].lower()
    years = profile["years_preparing"]
    stress = profile["main_stress"].lower()

    if "more than 6" in years or "5-6" in years:
        stage = "long-preparation transition"
    elif "less than 1" in years:
        stage = "early hedging"
    else:
        stage = "mid-preparation pivot"

    if any(token in background for token in ["b.tech", "btech", "computer", "information technology", "engineering", "mechanical", "electrical"]):
        base = "technical graduate"
    elif any(token in background for token in ["political", "economics", "ba"]):
        base = "social-science graduate"
    elif any(token in background for token in ["pharma", "pharmaceutical"]):
        base = "domain specialist"
    else:
        base = "generalist"

    urgency = "high" if any(token in stress for token in ["financial", "gap", "old", "family"]) else "medium"
    diagnosis = {
        "stage": stage,
        "base": base,
        "urgency": urgency,
        "core_problem": profile["main_stress"] or "unclear next step",
        "narrative": (
            f"This candidate is a {base} in a {stage} phase. The core transition blocker is "
            f"{profile['main_stress'] or 'lack of clarity'}, so the blueprint must reduce ambiguity, "
            "create quick proof of skill, and avoid long unfocused preparation cycles."
        ),
    }
    return {"diagnosis": diagnosis}


def extract_transferable_skills(state: AgentState) -> AgentState:
    profile = state["normalized"]
    skills = [
        "structured reading and synthesis",
        "long-form discipline under uncertainty",
        "current-affairs and governance awareness",
        "analytical writing",
        "exam-style quantitative reasoning",
        "self-study planning",
    ]
    interests = " ".join(profile.get("interests", [])).lower()
    background = profile.get("background", "").lower()
    if any(token in background for token in ["b.tech", "btech", "computer", "it", "engineering"]):
        skills.extend(["technical learning capacity", "systems thinking", "quantitative problem solving"])
    if "policy" in interests or "research" in interests:
        skills.extend(["policy framing", "research summarization"])
    if "data" in interests or "ai" in interests:
        skills.extend(["data curiosity", "automation mindset"])
    return {"skills": list(dict.fromkeys(skills))}


def research_market(state: AgentState) -> AgentState:
    settings = get_settings()
    profile = state["normalized"]
    queries = [
        f"site:ycombinator.com/jobs entry level AI operations data analyst skills {profile['background']}",
        "site:wellfound.com/jobs AI data analyst product operations startup skills India",
        "entry level AI analyst data analyst skills India 2026",
    ]
    signals: list[dict[str, str]] = []
    if settings.tavily_api_key:
        try:
            from tavily import TavilyClient

            client = TavilyClient(api_key=settings.tavily_api_key)
            for query in queries:
                result = client.search(query=query, max_results=3, search_depth="basic")
                for item in result.get("results", []):
                    signals.append(
                        {
                            "source": item.get("url", "Tavily"),
                            "title": item.get("title", "Market signal"),
                            "content": item.get("content", "")[:500],
                        }
                    )
        except Exception as exc:
            signals.append({"source": "Tavily unavailable", "title": str(exc), "content": ""})

    if not signals:
        signals = [
            {
                "source": "Fallback market model",
                "title": "AI-assisted data analysis, SQL, Python, automation, and product operations remain strong transition skills.",
                "content": "Use live Tavily search in production to refresh this evidence per candidate.",
            },
            {
                "source": "Fallback market model",
                "title": "Startups value proof-of-work portfolios more than exam-preparation narratives.",
                "content": "Roadmaps should include public projects, dashboards, case studies, and concise GitHub/Notion artifacts.",
            },
        ]
    return {"market": signals[:8]}


def generate_paths(state: AgentState) -> AgentState:
    profile = state["normalized"]
    diagnosis = state["diagnosis"]
    interests = " ".join(profile.get("interests", [])).lower()
    background = profile.get("background", "").lower()

    candidates = []
    if "data" in interests or "ai" in interests or "economics" in background:
        candidates.append(("Data Analyst", 88))
    if "ai" in interests or "product" in interests or "operations" in interests:
        candidates.append(("AI Product / Operations Analyst", 84))
    if "policy" in interests or "research" in interests or "political" in background or "pharma" in background:
        candidates.append(("Policy / Research Analyst", 82))
    if any(token in background for token in ["computer", "information technology", "btech computer", "software"]):
        candidates.append(("Software / AI Builder", 80))
    if not candidates:
        candidates = [("Data Analyst", 78), ("AI Product / Operations Analyst", 74), ("Policy / Research Analyst", 72)]

    for fallback in [("Policy / Research Analyst", 76), ("Data Analyst", 74), ("AI Product / Operations Analyst", 72), ("Software / AI Builder", 70)]:
        candidates.append(fallback)

    deduped: list[tuple[str, int]] = []
    seen = set()
    for title, score in sorted(candidates, key=lambda item: item[1], reverse=True):
        if title not in seen:
            seen.add(title)
            deduped.append((title, score))

    paths = []
    for rank, (title, score) in enumerate(deduped[:3], start=1):
        paths.append(
            {
                "rank": rank,
                "title": title,
                "score": score,
                "why": (
                    f"{title} fits because it converts the candidate's {diagnosis['base']} background, "
                    f"UPSC-style synthesis, and stated interests into visible market proof within 8-12 weeks."
                ),
                "proof_points": [
                    "Can be validated through a small portfolio before applying.",
                    "Does not require hiding the exam gap; the gap can be reframed as structured preparation.",
                    "Creates optionality across startups, services firms, nonprofits, and domain teams.",
                ],
            }
        )
    return {"paths": paths}


def build_roadmap(state: AgentState) -> AgentState:
    paths = state["paths"]
    primary = paths[0]["title"]
    topics = BASE_COURSES.get(primary, BASE_COURSES["Data Analyst"])
    weekly_plan = []
    for week in range(1, 13):
        topic = topics[(week - 1) % len(topics)]
        if week <= 4:
            phase = "Foundation"
        elif week <= 8:
            phase = "Portfolio"
        else:
            phase = "Applications"
        weekly_plan.append(
            {
                "week": week,
                "theme": f"{phase}: {topic}",
                "topics": [
                    topic,
                    "Create notes in public-proof format: Notion, GitHub README, or PDF case note.",
                    "Spend 3 hours applying the concept to an India-relevant dataset or workflow.",
                ],
                "output": f"One visible artifact connected to {primary.lower()}.",
            }
        )

    projects = [
        {
            "name": "UPSC Prep to Employability Dashboard",
            "description": "Analyze time spent, syllabus coverage, mock scores, and skill transfer into a dashboard that demonstrates analytics and storytelling.",
            "skills": ["Excel/Sheets", "data cleaning", "dashboarding", "narrative insight"],
        },
        {
            "name": "AI Career Research Agent",
            "description": "Build a small tool that searches jobs, extracts required skills, and summarizes weekly learning priorities.",
            "skills": ["Python", "APIs", "LLM prompting", "market research"],
        },
        {
            "name": "Policy or Market Brief",
            "description": "Write a 4-page evidence-backed brief on one public issue or startup sector using structured sources and charts.",
            "skills": ["research", "writing", "source evaluation", "visualization"],
        },
    ]
    return {"roadmap": {"weekly_plan": weekly_plan, "projects": projects}}


def write_blueprint(state: AgentState) -> AgentState:
    profile = state["normalized"]
    diagnosis = state["diagnosis"]
    tier = state.get("tier", "mini")
    language = state.get("language", "english")
    path_count = 1 if tier == "sample" else 3
    weekly_count = 4 if tier == "sample" else 12
    ai_blueprint = _try_ai_blueprint(state, path_count, weekly_count, language)
    if ai_blueprint:
        summary = f"Generated AI {tier} blueprint with {len(ai_blueprint.get('paths', []))} path(s) and {len(ai_blueprint.get('weekly_plan', []))} weekly steps."
        return {"blueprint": ai_blueprint, "summary": summary}

    blueprint = {
        "snapshot": {
            "age_group": profile.get("age_group", ""),
            "qualification": profile.get("qualification", ""),
            "background": profile.get("background", ""),
            "exam_history": profile.get("exams", ""),
            "current_situation": profile.get("current_situation", ""),
            "main_stress": profile.get("main_stress", ""),
            "interests": "; ".join(profile.get("interests", [])),
        },
        "diagnosis": diagnosis["narrative"],
        "strengths": state["skills"],
        "paths": state["paths"][:path_count],
        "weekly_plan": state["roadmap"]["weekly_plan"][:weekly_count],
        "projects": state["roadmap"]["projects"][: 1 if tier == "sample" else 3],
        "resume_bullets": [
            "Reframed competitive-exam preparation into structured research, high-volume self-learning, and analytical writing.",
            "Built portfolio projects demonstrating data analysis, AI-assisted research, and decision-support communication.",
            "Converted governance/current-affairs knowledge into business, policy, or product context depending on target role.",
        ],
        "market_signals": state["market"],
    }
    summary = f"Generated {tier} blueprint with {len(blueprint['paths'])} path(s) and {len(blueprint['weekly_plan'])} weekly steps."
    return {"blueprint": blueprint, "summary": summary}


def _try_ai_blueprint(state: AgentState, path_count: int, weekly_count: int, language: str) -> dict[str, Any] | None:
    prompt = _blueprint_prompt(state, path_count, weekly_count, language)
    parsed = complete_json(prompt, task="blueprint", temperature=0.35)
    if parsed is None:
        return None
    try:
        return _normalize_ai_blueprint(parsed, state, path_count, weekly_count)
    except Exception:
        return None


def _blueprint_prompt(state: AgentState, path_count: int, weekly_count: int, language: str) -> str:
    profile = state["normalized"]
    return f"""
You are an expert career transition strategist for Indian UPSC/competitive-exam aspirants moving into realistic careers.

Create a deeply personalized transition blueprint in {language}. Be practical, empathetic, specific, and market-aware.
Do not give generic motivation. Convert the candidate's exam years into credible career positioning.

Candidate profile JSON:
{json.dumps(profile, ensure_ascii=False, indent=2)}

Diagnosis:
{json.dumps(state["diagnosis"], ensure_ascii=False, indent=2)}

Transferable skills:
{json.dumps(state["skills"], ensure_ascii=False, indent=2)}

Initial career paths:
{json.dumps(state["paths"][:path_count], ensure_ascii=False, indent=2)}

Market signals from search:
{json.dumps(state["market"], ensure_ascii=False, indent=2)}

Return ONLY valid JSON with this exact schema:
{{
  "snapshot": {{
    "age_group": "...",
    "qualification": "...",
    "background": "...",
    "exam_history": "...",
    "current_situation": "...",
    "main_stress": "...",
    "interests": "..."
  }},
  "diagnosis": "A detailed 150-220 word diagnosis.",
  "strengths": ["8-12 transferable strengths"],
  "paths": [
    {{
      "rank": 1,
      "title": "Career path name",
      "score": 0,
      "why": "Specific fit rationale.",
      "proof_points": ["specific point", "specific point", "specific point"]
    }}
  ],
  "weekly_plan": [
    {{
      "week": 1,
      "theme": "Theme",
      "topics": ["course/topic 1", "course/topic 2", "course/topic 3"],
      "output": "Concrete weekly deliverable"
    }}
  ],
  "projects": [
    {{
      "name": "Project name",
      "description": "Specific project brief tied to hot market skills.",
      "skills": ["skill 1", "skill 2", "skill 3"]
    }}
  ],
  "resume_bullets": ["5 resume bullets"],
  "market_signals": [
    {{"source": "source name or URL", "title": "market signal"}}
  ]
}}

Constraints:
- Include exactly {path_count} career paths.
- Include exactly {weekly_count} weekly roadmap items.
- Include courses/topics week by week, not vague advice.
- Include projects based on AI/data/software/policy/product market demand where relevant.
- Make the plan realistic for someone with gap years and low confidence.
- Do not mention that you are an AI model.
"""


def _normalize_ai_blueprint(
    blueprint: dict[str, Any], state: AgentState, path_count: int, weekly_count: int
) -> dict[str, Any]:
    fallback = {
        "snapshot": {
            "age_group": state["normalized"].get("age_group", ""),
            "qualification": state["normalized"].get("qualification", ""),
            "background": state["normalized"].get("background", ""),
            "exam_history": state["normalized"].get("exams", ""),
            "current_situation": state["normalized"].get("current_situation", ""),
            "main_stress": state["normalized"].get("main_stress", ""),
            "interests": "; ".join(state["normalized"].get("interests", [])),
        },
        "diagnosis": state["diagnosis"]["narrative"],
        "strengths": state["skills"],
        "paths": state["paths"][:path_count],
        "weekly_plan": state["roadmap"]["weekly_plan"][:weekly_count],
        "projects": state["roadmap"]["projects"],
        "resume_bullets": [],
        "market_signals": state["market"],
    }
    for key, value in fallback.items():
        blueprint.setdefault(key, value)
    blueprint["paths"] = blueprint["paths"][:path_count]
    blueprint["weekly_plan"] = blueprint["weekly_plan"][:weekly_count]
    if not blueprint["projects"]:
        blueprint["projects"] = fallback["projects"]
    if not blueprint["market_signals"]:
        blueprint["market_signals"] = fallback["market_signals"]
    return blueprint


def export_pdf(state: AgentState) -> AgentState:
    candidate_id = int(state["candidate"]["id"])
    tier = state.get("tier", "mini")
    path = export_blueprint_pdf(state["blueprint"], candidate_id, tier)
    return {"pdf_path": str(path)}


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("normalize_profile", normalize_profile)
    graph.add_node("diagnose_candidate", diagnose_candidate)
    graph.add_node("extract_transferable_skills", extract_transferable_skills)
    graph.add_node("research_market", research_market)
    graph.add_node("generate_paths", generate_paths)
    graph.add_node("build_roadmap", build_roadmap)
    graph.add_node("write_blueprint", write_blueprint)
    graph.add_node("export_pdf", export_pdf)

    graph.set_entry_point("normalize_profile")
    graph.add_edge("normalize_profile", "diagnose_candidate")
    graph.add_edge("diagnose_candidate", "extract_transferable_skills")
    graph.add_edge("extract_transferable_skills", "research_market")
    graph.add_edge("research_market", "generate_paths")
    graph.add_edge("generate_paths", "build_roadmap")
    graph.add_edge("build_roadmap", "write_blueprint")
    graph.add_edge("write_blueprint", "export_pdf")
    graph.add_edge("export_pdf", END)
    return graph.compile()


career_graph = build_graph()


def run_blueprint(candidate: dict[str, Any], tier: str, language: str = "english") -> AgentState:
    return career_graph.invoke({"candidate": candidate, "tier": tier, "language": language})
