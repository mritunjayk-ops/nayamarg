"""Model gateway: one entry point for every LLM call in the app.

Callers ask for a completion by *task* (e.g. "blueprint", "resume"). The gateway
walks that task's provider fallback chain and uses the first provider that has an
API key configured and returns without error. If no provider is available, it
returns None so the caller can fall back to deterministic output — the app keeps
running even when only some (or no) provider keys are present.

Supported providers:
- "openai"    — OpenAI API (default for now).
- "groq"      — Groq's OpenAI-compatible API (fast, cheap open models). Reuses the
                OpenAI SDK with a different base URL, so no extra dependency.
- "anthropic" — Claude, for high-judgment work later. Optional; only used when
                ANTHROPIC_API_KEY is set.

To change routing (e.g. put Groq first for cheap high-volume tasks once its key is
set, or reserve Anthropic for a "synthesis" task), edit TASK_ROUTES below.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from app.config import Settings, get_settings

logger = logging.getLogger("nayamarg.model_gateway")

# Groq exposes an OpenAI-compatible endpoint, so the OpenAI SDK talks to it directly.
GROQ_BASE_URL = "https://api.groq.com/openai/v1"

# Ordered provider fallback chain per task. The gateway tries providers left to
# right and uses the first one that is configured and succeeds. Reorder to change
# routing — e.g. ["groq", "openai", "anthropic"] to prefer cheap Groq models.
TASK_ROUTES: dict[str, list[str]] = {
    "default": ["openai", "groq", "anthropic"],
    "blueprint": ["openai", "groq", "anthropic"],
    "resume": ["openai", "groq", "anthropic"],
}


def complete(prompt: str, task: str = "default", temperature: float = 0.3, max_tokens: int = 8000) -> str | None:
    """Return model text for `prompt`, trying each provider in the task's chain.

    Returns None if no provider is available or all providers fail.
    """
    settings = get_settings()
    for provider in TASK_ROUTES.get(task, TASK_ROUTES["default"]):
        try:
            if provider in ("openai", "groq"):
                text = _openai_compatible(provider, prompt, temperature, settings)
            elif provider == "anthropic":
                text = _anthropic(prompt, max_tokens, settings)
            else:
                continue
        except Exception as exc:  # any provider error -> try the next one
            logger.warning("provider=%s failed for task=%s: %s", provider, task, exc)
            continue
        if text:
            logger.info("task=%s served by provider=%s", task, provider)
            return text
    logger.warning("no model provider available for task=%s", task)
    return None


def complete_json(prompt: str, task: str = "default", temperature: float = 0.3, max_tokens: int = 8000) -> dict[str, Any] | None:
    """Like `complete`, but parse the response as a JSON object. None on failure."""
    text = complete(prompt, task=task, temperature=temperature, max_tokens=max_tokens)
    if not text:
        return None
    try:
        return _extract_json(text)
    except (json.JSONDecodeError, ValueError) as exc:
        logger.warning("JSON parse failed for task=%s: %s", task, exc)
        return None


def _openai_compatible(provider: str, prompt: str, temperature: float, settings: Settings) -> str | None:
    if provider == "openai":
        api_key, base_url, model = settings.openai_api_key, None, settings.openai_model
    else:  # groq
        api_key, base_url, model = settings.groq_api_key, GROQ_BASE_URL, settings.groq_model
    if not api_key:
        return None

    from openai import OpenAI

    client = OpenAI(api_key=api_key, base_url=base_url)
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
    )
    return response.choices[0].message.content


def _anthropic(prompt: str, max_tokens: int, settings: Settings) -> str | None:
    if not settings.anthropic_api_key:
        return None

    from anthropic import Anthropic

    client = Anthropic(api_key=settings.anthropic_api_key)
    # Current Claude models (Sonnet 5 etc.) reject `temperature`; omit it.
    response = client.messages.create(
        model=settings.anthropic_model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    parts = [block.text for block in response.content if getattr(block, "type", None) == "text"]
    return "".join(parts) if parts else None


def _extract_json(content: str) -> dict[str, Any]:
    """Best-effort extraction of a JSON object from a model response."""
    cleaned = content.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start >= 0 and end >= start:
        cleaned = cleaned[start : end + 1]
    return json.loads(cleaned)
