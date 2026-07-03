from typing import Any, TypedDict

from pydantic import BaseModel


class CandidateSummary(BaseModel):
    id: int
    age_group: str
    qualification: str
    background: str
    exams: str
    years_preparing: str
    current_situation: str
    main_stress: str
    interests: str
    blueprint_interest: str
    price_preference: str
    interview_interest: str


class GenerateRequest(BaseModel):
    candidate_id: int
    tier: str = "mini"
    language: str = "english"


class CandidateIntake(BaseModel):
    age_group: str = ""
    qualification: str = ""
    background: str = ""
    exams: str = ""
    years_preparing: str = ""
    current_situation: str = ""
    worries: str = ""
    main_stress: str = ""
    situation_words: str = ""
    interests: str = ""
    explored_alternative: str = ""
    alternative_path: str = ""
    value_rating: str = ""
    blueprint_interest: str = ""
    price_preference: str = ""
    trust_factor: str = ""
    free_blueprint: str = ""
    interview_interest: str = ""


class IntakeGenerateRequest(BaseModel):
    candidate: CandidateIntake
    tier: str = "mini"
    language: str = "english"


class GenerateResponse(BaseModel):
    candidate_id: int
    tier: str
    status: str
    pdf_url: str
    summary: str


class PaymentPlanResponse(BaseModel):
    provider: str
    local_mode: bool
    amount_inr: int
    amount_subunits: int
    steps: list[str]


class SystemStatusResponse(BaseModel):
    openai_configured: bool
    tavily_configured: bool
    razorpay_configured: bool
    mode: str


class JobItem(BaseModel):
    id: str
    source: str
    company: str = ""
    title: str
    location: str = ""
    remote: bool = True
    salary: str = ""
    tags: list[str] = []
    description: str = ""
    apply_url: str
    posted_at: str = ""


class JobSearchRequest(BaseModel):
    candidate: CandidateIntake
    role: str = ""
    location: str = ""
    remote_only: bool = True
    limit: int = 20


class JobSearchResponse(BaseModel):
    query: str
    jobs: list[JobItem]


class JobFitRequest(BaseModel):
    candidate: CandidateIntake
    jobs: list[JobItem]


class JobFitResult(BaseModel):
    job_id: str
    fit_score: int
    recommendation: str
    why_fit: str
    risks: list[str]
    missing_skills: list[str]
    resume_keywords: list[str]
    application_strategy: str


class JobFitResponse(BaseModel):
    results: list[JobFitResult]


class ResumeProject(BaseModel):
    name: str
    description: str
    bullets: list[str]
    skills: list[str]


class ResumeDocument(BaseModel):
    headline: str
    summary: str
    skills: list[str]
    projects: list[ResumeProject]
    education: list[str]
    experience: list[str]
    gap_positioning: str


class ResumeGenerateRequest(BaseModel):
    candidate: CandidateIntake
    target_role: str = "Data Analyst"
    job: JobItem | None = None


class ResumeGenerateResponse(BaseModel):
    resume: ResumeDocument
    pdf_url: str


class AgentState(TypedDict, total=False):
    candidate: dict[str, Any]
    tier: str
    language: str
    normalized: dict[str, Any]
    diagnosis: dict[str, Any]
    skills: list[str]
    market: list[dict[str, str]]
    paths: list[dict[str, Any]]
    roadmap: dict[str, Any]
    blueprint: dict[str, Any]
    pdf_path: str
    summary: str
