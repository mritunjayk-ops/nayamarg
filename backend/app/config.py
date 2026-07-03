from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel
import os


BACKEND_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR = BACKEND_DIR.parent
DATA_DIR = BACKEND_DIR / "data"
GENERATED_DIR = DATA_DIR / "generated"
SOURCE_CSV = ROOT_DIR / "Untitled form.csv"


class Settings(BaseModel):
    openai_api_key: str | None = None
    groq_api_key: str | None = None
    anthropic_api_key: str | None = None
    tavily_api_key: str | None = None
    razorpay_key_id: str | None = None
    razorpay_key_secret: str | None = None
    frontend_origin: str = "http://127.0.0.1:3000"
    # Model per provider — override in .env to swap models without code changes.
    openai_model: str = "gpt-4.1-mini"
    groq_model: str = "llama-3.3-70b-versatile"
    anthropic_model: str = "claude-sonnet-5"


@lru_cache
def get_settings() -> Settings:
    load_dotenv(BACKEND_DIR / ".env")
    return Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY") or None,
        groq_api_key=os.getenv("GROQ_API_KEY") or None,
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY") or None,
        tavily_api_key=os.getenv("TAVILY_API_KEY") or None,
        razorpay_key_id=os.getenv("RAZORPAY_KEY_ID") or None,
        razorpay_key_secret=os.getenv("RAZORPAY_KEY_SECRET") or None,
        frontend_origin=os.getenv("FRONTEND_ORIGIN") or "http://127.0.0.1:3000",
        openai_model=os.getenv("OPENAI_MODEL") or "gpt-4.1-mini",
        groq_model=os.getenv("GROQ_MODEL") or "llama-3.3-70b-versatile",
        anthropic_model=os.getenv("ANTHROPIC_MODEL") or "claude-sonnet-5",
    )
