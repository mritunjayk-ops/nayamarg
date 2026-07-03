import csv
import hashlib
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.config import SOURCE_CSV
from app.models import CandidateSummary


FIELD_ALIASES = {
    "age_group": "age group",
    "qualification": "highest qualification",
    "background": "degree / educational background",
    "exams": "exam(s)",
    "years_preparing": "How many years",
    "current_situation": "current situation",
    "worries": "what worries",
    "main_stress": "ONE of the above",
    "situation_words": "Describe your situation",
    "interests": "areas seem",
    "explored_alternative": "seriously explored",
    "alternative_path": "which career path",
    "value_rating": "how valuable",
    "blueprint_interest": "interested in receiving",
    "price_preference": "reasonable price",
    "trust_factor": "trust such a service",
    "email": "Email Address",
    "free_blueprint": "free personalized",
    "interview_interest": "15 minutes",
}


def _find_header(headers: list[str], needle: str) -> str:
    clean_needle = needle.lower()
    for header in headers:
        if clean_needle in header.lower():
            return header
    return ""


def _value(row: dict[str, str], header: str) -> str:
    return (row.get(header, "") or "").strip()


@lru_cache
def load_candidates(csv_path: str | Path = SOURCE_CSV) -> list[dict[str, Any]]:
    with Path(csv_path).open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        headers = reader.fieldnames or []
        mapped = {key: _find_header(headers, needle) for key, needle in FIELD_ALIASES.items()}
        candidates: list[dict[str, Any]] = []
        for index, row in enumerate(reader, start=1):
            normalized = {key: _value(row, header) for key, header in mapped.items()}
            normalized["id"] = index
            normalized["source_hash"] = hashlib.sha256(str(row).encode("utf-8")).hexdigest()[:12]
            candidates.append(normalized)
        return candidates


def list_candidate_summaries() -> list[CandidateSummary]:
    return [
        CandidateSummary(
            id=candidate["id"],
            age_group=candidate["age_group"],
            qualification=candidate["qualification"],
            background=candidate["background"],
            exams=candidate["exams"],
            years_preparing=candidate["years_preparing"],
            current_situation=candidate["current_situation"],
            main_stress=candidate["main_stress"],
            interests=candidate["interests"],
            blueprint_interest=candidate["blueprint_interest"],
            price_preference=candidate["price_preference"],
            interview_interest=candidate["interview_interest"],
        )
        for candidate in load_candidates()
    ]


def get_candidate(candidate_id: int) -> dict[str, Any]:
    for candidate in load_candidates():
        if candidate["id"] == candidate_id:
            return candidate
    raise KeyError(f"Candidate {candidate_id} not found")
