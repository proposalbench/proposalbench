"""Keep a Proposia run away from its production database (shared by the drivers).

Every database variable is blanked before the workflow is imported, and the run stops if any of
them comes back during import.
"""

from __future__ import annotations

DB_VARS = ("DATABASE_URL", "DIRECT_URL", "POSTGRES_URL", "REDIS_URL", "CELERY_BROKER_URL")


def _db_keys(environ) -> list[str]:
    return [k for k in environ if "SUPABASE" in k or k in DB_VARS]


def isolate_db_env(environ) -> None:
    """Blank every database variable. Blank, not deleted: libraries imported by the workflow
    call ``load_dotenv``, which restores deleted variables but never overrides existing ones."""
    for key in {*_db_keys(environ), *DB_VARS, "SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY"}:
        environ[key] = ""


def check_db_env(environ) -> None:
    leaked = [k for k in _db_keys(environ) if environ[k]]
    if leaked:
        raise SystemExit(f"database variables came back during import: {sorted(leaked)}")
