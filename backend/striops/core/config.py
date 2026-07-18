"""Application configuration, loaded from environment variables."""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


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

    # Postgres
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
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
            f"?connect_timeout={self.postgres_connect_timeout}"
        )

    @property
    def has_llm(self) -> bool:
        return bool(self.gemini_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
