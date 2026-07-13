"""Application settings, loaded from environment (see .env.example).

Convention over configuration: sensible defaults live here; env vars only
override what actually varies between environments.
"""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    app_name: str = "TripPilot AI"
    environment: Literal["local", "staging", "production"] = "local"
    debug: bool = True
    api_v1_prefix: str = "/api/v1"

    # CORS — explicit allowlist, never "*" in production (PROJECT_PLAN §5.7)
    cors_origins: list[str] = ["http://localhost:3000"]

    # Secrets / external services (populated per-environment; unset for now)
    openai_api_key: str = ""
    database_url: str = ""
    redis_url: str = ""


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
