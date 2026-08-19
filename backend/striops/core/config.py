"""Application configuration, loaded from environment variables."""
from __future__ import annotations

from functools import lru_cache
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from pydantic_settings import BaseSettings, SettingsConfigDict


def _is_local_postgres_host(host: str) -> bool:
    return host in ("localhost", "127.0.0.1", "::1", "postgres")


def build_postgres_dsn(
    *,
    database_url: str = "",
    postgres_user: str = "striops",
    postgres_password: str = "striops",
    postgres_host: str = "localhost",
    postgres_port: int = 5432,
    postgres_db: str = "striops",
    postgres_connect_timeout: int = 5,
) -> str:
    """Compose a libpq URI. ``DATABASE_URL`` wins when set (Neon, Render, etc.).

    Managed hosts require TLS. Local Docker does not. ``sslmode=require`` is
    added for any non-local host that did not already specify one, so a Neon
    URI without the query string still connects instead of silently falling
    back to seed.
    """
    if database_url.strip():
        parsed = urlparse(database_url.strip())
        host = parsed.hostname or ""
        qs = dict(parse_qsl(parsed.query, keep_blank_values=True))
        qs.setdefault("connect_timeout", str(postgres_connect_timeout))
        if not _is_local_postgres_host(host):
            qs.setdefault("sslmode", "require")
        return urlunparse(parsed._replace(query=urlencode(qs)))

    qs = {"connect_timeout": str(postgres_connect_timeout)}
    if not _is_local_postgres_host(postgres_host):
        qs["sslmode"] = "require"
    return (
        f"postgresql://{postgres_user}:{postgres_password}"
        f"@{postgres_host}:{postgres_port}/{postgres_db}?{urlencode(qs)}"
    )


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    striops_env: str = "development"
    striops_log_level: str = "INFO"
    striops_municipality: str = "CPT"
    # LLM-backed briefs are cached in-process for this long (0 disables).
    striops_brief_ttl_seconds: int = 3600

    # LLM / Gemini
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    gemini_embed_model: str = "text-embedding-004"

    # Postgres — prefer DATABASE_URL (Neon). The split POSTGRES_* vars remain
    # for docker-compose. Do not commit either.
    database_url: str = ""
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "striops"
    postgres_user: str = "striops"
    postgres_password: str = "striops"

    # Neo4j
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "striops-strategic-twin"

    # Fail fast if Postgres is unreachable (e.g. still provisioning on first
    # deploy) so startup never blocks on a hanging TCP handshake — the app
    # falls back to seed until the database is ready.
    postgres_connect_timeout: int = 5

    @property
    def postgres_dsn(self) -> str:
        return build_postgres_dsn(
            database_url=self.database_url,
            postgres_user=self.postgres_user,
            postgres_password=self.postgres_password,
            postgres_host=self.postgres_host,
            postgres_port=self.postgres_port,
            postgres_db=self.postgres_db,
            postgres_connect_timeout=self.postgres_connect_timeout,
        )

    @property
    def has_llm(self) -> bool:
        return bool(self.gemini_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
