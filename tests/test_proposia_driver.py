import importlib.util
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parents[1] / "tools" / "proposia"


def _load(name: str):
    path = TOOLS / f"{name}.py"
    if not path.exists():
        pytest.skip(f"{path.name} is not part of this copy")
    spec = importlib.util.spec_from_file_location(f"proposia_{name}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_database_variables_are_blanked_not_deleted():
    driver = _load("db_guard")
    env = {"SUPABASE_URL": "https://x", "NEXT_PUBLIC_SUPABASE_URL": "u", "DATABASE_URL": "pg"}
    driver.isolate_db_env(env)
    assert env["SUPABASE_URL"] == env["NEXT_PUBLIC_SUPABASE_URL"] == env["DATABASE_URL"] == ""
    # A later load_dotenv(override=False) keeps blank values; a deleted key would come back.
    assert "SUPABASE_SERVICE_ROLE_KEY" in env and "REDIS_URL" in env
    driver.check_db_env(env)


def test_restored_credentials_abort_the_run():
    driver = _load("db_guard")
    env = {}
    driver.isolate_db_env(env)
    env["SUPABASE_SERVICE_ROLE_KEY"] = "secret"
    with pytest.raises(SystemExit, match="SUPABASE_SERVICE_ROLE_KEY"):
        driver.check_db_env(env)


def test_shown_text_prefers_the_checked_final_draft():
    driver = _load("driver")
    state = {
        "final_proposal": "pre-check text",
        "proposal_draft": {"v3_final_with_citations": "checked text", "v1_full_text": "draft"},
    }
    assert driver.shown_text(state) == ("checked text", "proposal_draft.v3_final_with_citations")
    assert driver.shown_text({"proposal_draft": {"v1_full_text": "draft"}})[1] == (
        "proposal_draft.v1_full_text"
    )
    assert driver.shown_text({}) == ("", "none")
