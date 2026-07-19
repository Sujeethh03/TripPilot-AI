"""Application settings, loaded from environment (see .env.example).

Convention over configuration: sensible defaults live here; env vars only
override what actually varies between environments.
"""

from functools import lru_cache
from typing import Literal

from pydantic import field_validator
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
    openweather_key: str = ""
    database_url: str = ""
    redis_url: str = ""
    # Google OAuth: the frontend's Google Sign-In client id. ID tokens are
    # accepted only if their audience matches this (unset disables Google auth).
    google_client_id: str = ""
    # Google Maps Platform key for the Places + Directions MCP servers.
    google_maps_key: str = ""

    # OpenAI model routing (PROJECT_PLAN §9 cost controls): cheap model for
    # routing/extraction, capable model for planning/synthesis.
    model_router: str = "gpt-4o-mini"
    model_planner: str = "gpt-4o"

    # Conversation memory backend. "memory" (default) keeps state in-process;
    # "postgres" persists LangGraph checkpoints so conversations survive restarts.
    checkpointer: Literal["memory", "postgres"] = "memory"

    # Auth (PROJECT_PLAN §5.7). Override jwt_secret per-environment; the default
    # is for local dev only.
    jwt_secret: str = "dev-secret-change-me-in-production-please-32b+"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24

    @field_validator("database_url")
    @classmethod
    def _use_asyncpg_driver(cls, value: str) -> str:
        """Coerce a plain ``postgresql://`` URL to the asyncpg driver.

        Managed hosts (Render, Neon, Heroku) hand out driver-less URLs, but our
        engine is async. Normalising here means the deploy can wire the host's
        connection string straight through without hand-editing it.
        """
        for prefix in ("postgresql://", "postgres://"):
            if value.startswith(prefix):
                return "postgresql+asyncpg://" + value[len(prefix) :]
        return value

    @property
    def postgres_dsn(self) -> str:
        """psycopg-style DSN (the checkpointer uses psycopg, not asyncpg)."""
        return self.database_url.replace("+asyncpg", "")


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
