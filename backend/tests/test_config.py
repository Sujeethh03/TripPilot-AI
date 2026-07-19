"""Settings normalisation."""

from app.config import Settings


def test_plain_postgres_url_gets_asyncpg_driver() -> None:
    """Managed hosts hand out driver-less URLs; our engine needs asyncpg."""
    settings = Settings(database_url="postgresql://u:p@host:5432/db")
    assert settings.database_url == "postgresql+asyncpg://u:p@host:5432/db"


def test_legacy_postgres_scheme_is_normalised() -> None:
    settings = Settings(database_url="postgres://u:p@host:5432/db")
    assert settings.database_url == "postgresql+asyncpg://u:p@host:5432/db"


def test_explicit_driver_is_left_alone() -> None:
    url = "postgresql+asyncpg://u:p@host:5432/db"
    assert Settings(database_url=url).database_url == url


def test_postgres_dsn_strips_driver_for_psycopg() -> None:
    """The LangGraph checkpointer uses psycopg, which rejects the +asyncpg tag."""
    settings = Settings(database_url="postgresql://u:p@host:5432/db")
    assert settings.postgres_dsn == "postgresql://u:p@host:5432/db"
