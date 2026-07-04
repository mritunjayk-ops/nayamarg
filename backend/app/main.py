from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from app.agent_graph import run_blueprint
from app.config import GENERATED_DIR, get_settings
from app.data_loader import get_candidate, list_candidate_summaries
from app.job_search import score_jobs, search_jobs
from app.models import (
    GenerateRequest,
    GenerateResponse,
    IntakeGenerateRequest,
    JobFitRequest,
    JobFitResponse,
    JobSearchRequest,
    JobSearchResponse,
    PaymentPlanResponse,
    ResumeGenerateRequest,
    ResumeGenerateResponse,
    SystemStatusResponse,
)
from app.resume import export_resume_pdf, generate_resume


app = FastAPI(title="NayaMarg", version="0.1.0")

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_origin,
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/status", response_model=SystemStatusResponse)
def status():
    settings = get_settings()
    openai_configured = bool(settings.openai_api_key)
    tavily_configured = bool(settings.tavily_api_key)
    razorpay_configured = bool(settings.razorpay_key_id and settings.razorpay_key_secret)
    mode = "ai_search_payment_ready" if all([openai_configured, tavily_configured, razorpay_configured]) else "local_incomplete_config"
    return SystemStatusResponse(
        openai_configured=openai_configured,
        tavily_configured=tavily_configured,
        razorpay_configured=razorpay_configured,
        mode=mode,
    )


@app.get("/api/candidates")
def candidates():
    return list_candidate_summaries()


@app.get("/api/candidates/{candidate_id}")
def candidate_detail(candidate_id: int):
    try:
        candidate = get_candidate(candidate_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    public = {key: value for key, value in candidate.items() if key != "email"}
    return public


@app.post("/api/generate", response_model=GenerateResponse)
def generate(request: GenerateRequest):
    if request.tier not in {"sample", "mini"}:
        raise HTTPException(status_code=400, detail="tier must be sample or mini")
    if request.language.lower() not in {"english", "hinglish", "hindi"}:
        raise HTTPException(status_code=400, detail="Unsupported language")
    try:
        candidate = get_candidate(request.candidate_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    result = run_blueprint(candidate, request.tier, request.language)
    pdf_path = Path(result["pdf_path"])
    return GenerateResponse(
        candidate_id=request.candidate_id,
        tier=request.tier,
        status="ready",
        pdf_url=f"/api/pdfs/{pdf_path.name}",
        summary=result["summary"],
        blueprint=result.get("blueprint"),
    )


@app.post("/api/intake/generate", response_model=GenerateResponse)
def generate_from_intake(request: IntakeGenerateRequest):
    if request.tier not in {"sample", "mini"}:
        raise HTTPException(status_code=400, detail="tier must be sample or mini")
    if request.language.lower() not in {"english", "hinglish", "hindi"}:
        raise HTTPException(status_code=400, detail="Unsupported language")

    candidate = request.candidate.model_dump()
    candidate["id"] = 0
    result = run_blueprint(candidate, request.tier, request.language)
    pdf_path = Path(result["pdf_path"])
    return GenerateResponse(
        candidate_id=0,
        tier=request.tier,
        status="ready",
        pdf_url=f"/api/pdfs/{pdf_path.name}",
        summary=result["summary"],
        blueprint=result.get("blueprint"),
    )


@app.get("/api/pdfs/{filename}")
def get_pdf(filename: str):
    path = GENERATED_DIR / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="PDF not found")
    return FileResponse(path, media_type="application/pdf", filename=filename)


@app.post("/api/jobs/search", response_model=JobSearchResponse)
async def jobs_search(request: JobSearchRequest):
    query, jobs = await search_jobs(
        request.candidate,
        role=request.role,
        location=request.location,
        remote_only=request.remote_only,
        limit=request.limit,
    )
    return JobSearchResponse(query=query, jobs=jobs)


@app.post("/api/jobs/score", response_model=JobFitResponse)
def jobs_score(request: JobFitRequest):
    return JobFitResponse(results=score_jobs(request.candidate, request.jobs))


@app.post("/api/resumes/generate", response_model=ResumeGenerateResponse)
def resumes_generate(request: ResumeGenerateRequest):
    resume = generate_resume(request.candidate, request.target_role, request.job)
    safe_role = "".join(ch if ch.isalnum() else "_" for ch in request.target_role.lower()).strip("_") or "resume"
    path = export_resume_pdf(resume, filename=f"resume_{safe_role}.pdf")
    return ResumeGenerateResponse(resume=resume, pdf_url=f"/api/pdfs/{path.name}")


@app.get("/api/payment-plan", response_model=PaymentPlanResponse)
def payment_plan():
    settings = get_settings()
    return PaymentPlanResponse(
        provider="Razorpay",
        local_mode=not bool(settings.razorpay_key_id and settings.razorpay_key_secret),
        amount_inr=99,
        amount_subunits=9900,
        steps=[
            "Create Razorpay order on the backend for INR 99.",
            "Open Razorpay Checkout from the frontend with the returned order ID.",
            "Verify payment signature on callback.",
            "Use webhook confirmation before unlocking paid PDF delivery.",
        ],
    )
