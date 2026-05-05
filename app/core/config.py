"""
Core application configuration.
Loads settings from environment variables using Pydantic BaseSettings.
All secrets (API keys) must be provided via environment — never hardcoded.
"""
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # ── Application ──────────────────────────────────────────────
    application_name: str = "AI Resume Analyzer API"
    application_version: str = "1.0.0"
    application_description: str = (
        "Upload a resume PDF and receive a structured LLM-powered analysis "
        "including skills, strengths, weaknesses, suggestions, and a score."
    )
    debug: bool = False

    # ── OpenAI (commented out — uncomment when client provides key) ──
    # openai_api_key: str = ""
    # openai_model: str = "gpt-4o-mini"
    # openai_max_tokens: int = 1500
    # openai_temperature: float = 0.3

    # ── Gemini (commented out — uncomment when client provides key) ──
    # gemini_api_key: str = ""
    # gemini_model: str = "gemini-2.0-flash"
    # gemini_max_tokens: int = 1500
    # gemini_temperature: float = 0.3

    # ── File Upload Constraints ───────────────────────────────────
    max_file_size_bytes: int = 5 * 1024 * 1024  # 5 MB hard limit
    allowed_content_types: list[str] = ["application/pdf"]

    # ── Rate Limiting ─────────────────────────────────────────────
    rate_limit_requests_per_minute: int = 10

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache()
def get_settings() -> Settings:
    """
    Return a cached singleton of Settings.
    lru_cache ensures the .env file is read exactly once at startup.
    """
    return Settings()