"""DATABASE_URL / SSL composition — Neon must not silently fall back to seed."""
from striops.core.config import build_postgres_dsn


def test_database_url_wins_over_split_vars():
    dsn = build_postgres_dsn(
        database_url="postgresql://neondb_owner:secret@ep-example.aws.neon.tech/neondb",
        postgres_host="localhost",
        postgres_db="ignored",
    )
    assert dsn.startswith("postgresql://neondb_owner:secret@ep-example.aws.neon.tech/neondb?")
    assert "sslmode=require" in dsn
    assert "connect_timeout=5" in dsn


def test_existing_sslmode_is_preserved():
    dsn = build_postgres_dsn(
        database_url="postgresql://u:p@db.neon.tech/neondb?sslmode=verify-full",
    )
    assert "sslmode=verify-full" in dsn
    assert "sslmode=require" not in dsn


def test_local_docker_does_not_force_tls():
    dsn = build_postgres_dsn(postgres_host="postgres")
    assert "sslmode" not in dsn
    assert "connect_timeout=5" in dsn


def test_split_vars_to_a_remote_host_still_require_tls():
    dsn = build_postgres_dsn(postgres_host="ep-example.aws.neon.tech")
    assert "sslmode=require" in dsn
