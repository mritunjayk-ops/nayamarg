from __future__ import annotations

import hashlib
import re
from typing import Any

import httpx

from app.config import get_settings
from app.models import CandidateIntake, JobItem


SKILL_TERMS = [
    "python",
    "sql",
    "excel",
    "power bi",
    "tableau",
    "analytics",
    "data analysis",
    "machine learning",
    "llm",
    "ai",
    "automation",
    "api",
    "fastapi",
    "javascript",
    "product",
    "operations",
    "research",
    "policy",
    "writing",
    "finance",
    "statistics",
    "dashboard",
    "communication",
]


def build_query(candidate: CandidateIntake, role: str = "") -> str:
    if role.strip():
        return role.strip()
    interests = candidate.interests.lower()
    background = candidate.background.lower()
    if "policy" in interests or "political" in background:
        return "policy research analyst"
    if "product" in interests or "operations" in interests:
        return "ai product operations analyst"
    if "software" in interests or "computer" in background or "information technology" in background:
        return "junior ai software developer"
    if "ai" in interests or "machine learning" in interests:
        return "ai data analyst"
    return "data analyst"


async def search_jobs(candidate: CandidateIntake, role: str = "", location: str = "", remote_only: bool = True, limit: int = 20) -> tuple[str, list[JobItem]]:
    query = build_query(candidate, role)
    jobs: list[JobItem] = []
    async with httpx.AsyncClient(timeout=12, follow_redirects=True) as client:
        jobs.extend(await _remoteok(client, query))
        jobs.extend(await _remotive(client, query))
    jobs.extend(_tavily_jobs(query, location))
    deduped = _dedupe(jobs)
    if remote_only:
        deduped = [job for job in deduped if job.remote]
    if not deduped:
        deduped = _fallback_search_leads(query, location)
    return query, deduped[: max(1, min(limit, 50))]


async def _remoteok(client: httpx.AsyncClient, query: str) -> list[JobItem]:
    url = "https://remoteok.com/api"
    try:
        response = await client.get(url, headers={"User-Agent": "NayaMarg/0.1"})
        response.raise_for_status()
        payload = response.json()
    except Exception:
        return []

    jobs: list[JobItem] = []
    query_terms = _terms(query)
    for raw in payload:
        if not isinstance(raw, dict) or "position" not in raw:
            continue
        text = " ".join(
            [
                str(raw.get("position", "")),
                str(raw.get("company", "")),
                " ".join(raw.get("tags") or []),
                str(raw.get("description", "")),
            ]
        ).lower()
        if query_terms and not any(term in text for term in query_terms):
            continue
        salary = _salary(raw.get("salary_min"), raw.get("salary_max"))
        apply_url = raw.get("apply_url") or raw.get("url") or ""
        if not apply_url:
            continue
        jobs.append(
            JobItem(
                id=_job_id("remoteok", apply_url),
                source="Remote OK",
                company=str(raw.get("company", "")),
                title=str(raw.get("position", "")),
                location=str(raw.get("location", "Remote")),
                remote=True,
                salary=salary,
                tags=[str(tag) for tag in raw.get("tags") or []],
                description=_clean(raw.get("description", "")),
                apply_url=apply_url,
                posted_at=str(raw.get("date", "")),
            )
        )
    return jobs[:20]


async def _remotive(client: httpx.AsyncClient, query: str) -> list[JobItem]:
    try:
        response = await client.get("https://remotive.com/api/remote-jobs", params={"search": query})
        response.raise_for_status()
        payload = response.json()
    except Exception:
        return []

    jobs: list[JobItem] = []
    for raw in payload.get("jobs", [])[:20]:
        apply_url = raw.get("url") or ""
        if not apply_url:
            continue
        tags = raw.get("tags") or []
        if isinstance(tags, str):
            tags = [tags]
        jobs.append(
            JobItem(
                id=_job_id("remotive", apply_url),
                source="Remotive",
                company=str(raw.get("company_name", "")),
                title=str(raw.get("title", "")),
                location=str(raw.get("candidate_required_location", "Remote")),
                remote=True,
                salary=str(raw.get("salary", "") or ""),
                tags=[str(tag) for tag in tags],
                description=_clean(raw.get("description", "")),
                apply_url=apply_url,
                posted_at=str(raw.get("publication_date", "")),
            )
        )
    return jobs


def _tavily_jobs(query: str, location: str = "") -> list[JobItem]:
    settings = get_settings()
    if not settings.tavily_api_key:
        return []
    try:
        from tavily import TavilyClient

        client = TavilyClient(api_key=settings.tavily_api_key)
        search_query = (
            f'("{query}" OR "{query} remote") jobs apply '
            f"site:crossover.com/jobs OR site:ycombinator.com/jobs OR site:wellfound.com/jobs {location}"
        )
        result = client.search(query=search_query, max_results=8, search_depth="basic")
    except Exception:
        return []

    jobs: list[JobItem] = []
    for item in result.get("results", []):
        url = item.get("url", "")
        title = item.get("title", "Remote role")
        if not url:
            continue
        source = "Tavily"
        if "crossover.com" in url:
            source = "Crossover"
        elif "ycombinator.com" in url:
            source = "Y Combinator"
        elif "wellfound.com" in url:
            source = "Wellfound"
        jobs.append(
            JobItem(
                id=_job_id(source.lower(), url),
                source=source,
                company="",
                title=title,
                location=location or "Remote / varies",
                remote=True,
                tags=_extract_skills(item.get("content", "") + " " + title),
                description=item.get("content", ""),
                apply_url=url,
            )
        )
    return jobs


def score_jobs(candidate: CandidateIntake, jobs: list[JobItem]) -> list[dict[str, Any]]:
    candidate_text = " ".join(
        [
            candidate.background,
            candidate.interests,
            candidate.situation_words,
            candidate.alternative_path,
            candidate.exams,
        ]
    ).lower()
    candidate_skills = set(_extract_skills(candidate_text))
    results = []
    for job in jobs:
        job_text = " ".join([job.title, job.description, " ".join(job.tags)]).lower()
        job_skills = set(_extract_skills(job_text))
        matched = candidate_skills.intersection(job_skills)
        missing = sorted(job_skills.difference(candidate_skills))[:8]
        score = 45
        score += min(25, len(matched) * 5)
        score += 10 if any(term in job_text for term in ["junior", "entry", "associate", "intern", "trainee"]) else 0
        score += 8 if "remote" in (job.location or "").lower() or job.remote else 0
        score -= 12 if any(term in job_text for term in ["senior", "lead", "principal", "staff engineer", "5+ years"]) else 0
        score += _interest_bonus(candidate.interests.lower(), job_text)
        score = max(20, min(95, score))
        if score >= 72:
            recommendation = "apply_now"
        elif score >= 55:
            recommendation = "build_then_apply"
        else:
            recommendation = "skip_for_now"
        results.append(
            {
                "job_id": job.id,
                "fit_score": score,
                "recommendation": recommendation,
                "why_fit": _why_fit(candidate, job, matched),
                "risks": _risks(job_text, missing),
                "missing_skills": missing,
                "resume_keywords": sorted(job_skills.union(matched))[:12],
                "application_strategy": _application_strategy(recommendation, job, missing),
            }
        )
    return sorted(results, key=lambda item: item["fit_score"], reverse=True)


def _terms(query: str) -> list[str]:
    return [term for term in re.split(r"[^a-z0-9+#.]+", query.lower()) if len(term) > 2]


def _extract_skills(text: str) -> list[str]:
    lowered = text.lower()
    return [term for term in SKILL_TERMS if term in lowered]


def _salary(minimum: Any, maximum: Any) -> str:
    if minimum and maximum:
        return f"{minimum}-{maximum}"
    if minimum:
        return str(minimum)
    if maximum:
        return str(maximum)
    return ""


def _clean(value: Any) -> str:
    text = re.sub(r"<[^>]+>", " ", str(value or ""))
    text = re.sub(r"\s+", " ", text).strip()
    return text[:1800]


def _job_id(source: str, url: str) -> str:
    return hashlib.sha256(f"{source}:{url}".encode("utf-8")).hexdigest()[:16]


def _dedupe(jobs: list[JobItem]) -> list[JobItem]:
    seen = set()
    deduped = []
    for job in jobs:
        key = job.apply_url.lower().strip() or f"{job.source}:{job.company}:{job.title}".lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(job)
    return deduped


def _fallback_search_leads(query: str, location: str = "") -> list[JobItem]:
    encoded = query.replace(" ", "+")
    location_text = location or "Remote"
    leads = [
        (
            "Remote OK",
            f"https://remoteok.com/remote-{encoded}-jobs",
            f"Search Remote OK for {query}",
            "Remote OK search lead generated because live job APIs were unavailable in the local environment.",
        ),
        (
            "Remotive",
            f"https://remotive.com/remote-jobs/search?search={encoded}",
            f"Search Remotive for {query}",
            "Remotive search lead generated because live job APIs were unavailable in the local environment.",
        ),
        (
            "Crossover",
            "https://www.crossover.com/jobs",
            f"Search Crossover for {query}",
            "Crossover often lists remote roles with structured assessments. Review fit carefully before applying.",
        ),
        (
            "Y Combinator",
            f"https://www.ycombinator.com/jobs?query={encoded}",
            f"Search YC startups for {query}",
            "YC startup jobs can be useful for AI, data, operations, product, and software transition paths.",
        ),
        (
            "Wellfound",
            f"https://wellfound.com/jobs",
            f"Search Wellfound for {query}",
            "Wellfound startup jobs are useful for early-stage roles where portfolio proof can matter.",
        ),
    ]
    return [
        JobItem(
            id=_job_id(source.lower(), url),
            source=source,
            company=source,
            title=title,
            location=location_text,
            remote=True,
            tags=_extract_skills(f"{query} {description}"),
            description=description,
            apply_url=url,
        )
        for source, url, title, description in leads
    ]


def _interest_bonus(interests: str, job_text: str) -> int:
    bonus = 0
    if "ai" in interests and any(term in job_text for term in ["ai", "llm", "machine learning"]):
        bonus += 8
    if "data" in interests and any(term in job_text for term in ["data", "analytics", "sql"]):
        bonus += 8
    if "policy" in interests and any(term in job_text for term in ["policy", "research", "governance"]):
        bonus += 8
    if "product" in interests and "product" in job_text:
        bonus += 6
    return min(bonus, 14)


def _why_fit(candidate: CandidateIntake, job: JobItem, matched: set[str]) -> str:
    matched_text = ", ".join(sorted(matched)) if matched else "research, structured learning, and communication"
    return (
        f"This role can be positioned around the candidate's {candidate.background or 'academic'} background, "
        f"competitive-exam discipline, and visible overlap in {matched_text}. The application should translate "
        "UPSC preparation into research, analysis, written synthesis, and self-learning rather than apologizing for the gap."
    )


def _risks(job_text: str, missing: list[str]) -> list[str]:
    risks = []
    if any(term in job_text for term in ["senior", "lead", "principal", "5+ years"]):
        risks.append("Role may expect more experience than the candidate currently has.")
    if missing:
        risks.append(f"Skill gaps to address: {', '.join(missing[:4])}.")
    if not risks:
        risks.append("Candidate still needs a tailored resume and proof-of-work project before applying.")
    return risks


def _application_strategy(recommendation: str, job: JobItem, missing: list[str]) -> str:
    if recommendation == "apply_now":
        return f"Apply with a tailored resume emphasizing projects and keywords from {job.title}. Add a concise gap-year explanation."
    if recommendation == "build_then_apply":
        return f"Spend 2-4 weeks closing gaps in {', '.join(missing[:3]) or 'role-specific tools'}, then apply with a project artifact."
    return "Save for later. Use this job description to guide learning, but prioritize more entry-level roles first."
