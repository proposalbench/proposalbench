import json
from pathlib import Path

from proposalbench.systems.base import ModelUsage, SubmissionMeta
from proposalbench.systems.cli import CliSystem, _account, _contamination
from proposalbench.systems.registry import load_system
from proposalbench.tasks.loader import DATA_ROOT


def test_configs_and_commands():
    codex = load_system("cli-codex-gpt-6-astra")
    claude = load_system("cli-claude-code-opus")
    assert isinstance(codex, CliSystem) and isinstance(claude, CliSystem)
    cmd = claude._command(Path("/tmp/x"))
    assert "--restricted" in cmd and "--strict-mcp-config" in cmd and "Bash" not in " ".join(cmd)
    assert codex._command(Path("/tmp/x"))[-1] == "-"


def test_contamination_audit():
    assert _contamination(f"read {DATA_ROOT}/public/tasks/x/task.yaml") is not None
    assert _contamination("opened dossier.yaml") == "dossier.yaml"
    assert _contamination("wrote proposal.md") is None


def test_usage_accounting():
    usage, meta = ModelUsage("opus", "anthropic"), SubmissionMeta("s", "v", "t", "public", 1, "ok")
    result = {
        "type": "result",
        "usage": {"input_tokens": 10, "cache_read_input_tokens": 5, "output_tokens": 7},
        "num_turns": 3,
        "total_cost_usd": 0.42,
        "modelUsage": {"claude-opus-5-5": {}},
    }
    _account("claude", json.dumps(result), usage, meta)
    assert (usage.input_tokens, usage.output_tokens, usage.calls) == (15, 7, 3)
    assert usage.cached_input_tokens == 5
    assert meta.cost_usd == 0.42 and "claude-opus-5-5" in meta.notes[0]
    usage = ModelUsage("gpt-6-astra", "openai")
    events = [
        {"type": "turn.completed", "usage": {"input_tokens": 100, "output_tokens": 20}},
        {
            "type": "turn.completed",
            "usage": {"input_tokens": 300, "cached_input_tokens": 250, "output_tokens": 5},
        },
    ]
    _account("codex", "\n".join(json.dumps(e) for e in events), usage, meta)
    assert (usage.input_tokens, usage.output_tokens, usage.cached_input_tokens) == (400, 25, 250)


def test_meta_without_cached_tokens_still_loads():
    old = SubmissionMeta("s", "v", "t", "public", 1, "ok", models=[ModelUsage("m", "f", 1, 9, 3)])
    data = json.loads(old.to_json())
    del data["models"][0]["cached_input_tokens"]
    assert SubmissionMeta.from_json(json.dumps(data)).models[0].cached_input_tokens is None


def test_model_track_configs_are_direct():
    for name in ("direct-cc-claude-opus-5.5", "direct-codex-gpt-6-astra"):
        system = load_system(name)
        assert system.mode == "direct"
    cmd = load_system("direct-cc-claude-haiku-5.5")._command(Path("/tmp/x"))
    assert cmd[cmd.index("--tools") + 1] == "" and "--system-prompt" in cmd
    codex = load_system("direct-codex-gpt-6-sol")._command(Path("/tmp/x"))
    assert "tools.web_search=false" in codex and "-o" in codex


def test_usage_limit_detection():
    from proposalbench.systems.cli import usage_limit

    limited = {
        "type": "result",
        "is_error": True,
        "result": "You've hit your session limit · resets 5pm (Europe/Madrid)",
    }
    assert usage_limit(json.dumps(limited), "").startswith("You've hit your session limit")
    # A proposal that mentions rate limits is not an error.
    ok = {"type": "result", "is_error": False, "result": "API usage limit reached in the pilot"}
    assert usage_limit(json.dumps(ok), "") is None
    other = {"type": "result", "is_error": True, "result": "API Error: 500 overloaded"}
    assert usage_limit(json.dumps(other), "") is None


def test_a_run_folder_takes_its_codex_home_with_it():
    from proposalbench.systems.cli import _codex_home, _run_folder

    with _run_folder() as folder:
        home = _codex_home(folder)
        (home / "cache").mkdir(parents=True)
    assert not folder.exists() and not home.exists()


def _assistant(*blocks):
    return json.dumps({"type": "assistant", "message": {"content": list(blocks)}})


def test_direct_text_joins_every_turn_of_a_long_answer():
    from proposalbench.systems.cli import _direct_text

    stream = "\n".join(
        [
            json.dumps({"type": "system", "subtype": "init", "cwd": "/tmp/x"}),
            _assistant({"type": "thinking", "thinking": "plan"}),
            _assistant({"type": "text", "text": "# Title\n\nThe first half of a sent"}),
            json.dumps({"type": "user", "message": {"content": "Resume directly"}}),
            _assistant({"type": "text", "text": "ence, and the rest."}),
            json.dumps({"type": "result", "is_error": False, "result": "ence, and the rest."}),
        ]
    )
    assert _direct_text(stream) == "# Title\n\nThe first half of a sentence, and the rest."


def test_direct_text_keeps_only_the_last_full_write():
    from proposalbench.systems.cli import _direct_text

    stream = "\n".join(
        [
            _assistant({"type": "text", "text": "# Title\n\nAbandoned dra"}),
            _assistant({"type": "text", "text": "# Title\n\nThe complete proposal."}),
        ]
    )
    assert _direct_text(stream) == "# Title\n\nThe complete proposal."


def test_direct_claude_streams_and_ignores_user_instructions():
    cmd = load_system("direct-cc-claude-haiku-5.5")._command(Path("/tmp/x"))
    assert cmd[cmd.index("--output-format") + 1] == "stream-json" and "--verbose" in cmd


def test_a_usage_limit_is_an_infrastructure_failure(monkeypatch):
    import subprocess

    import pytest

    from proposalbench.llm import InfrastructureError
    from proposalbench.systems import cli
    from proposalbench.tasks.loader import Repository

    limited = json.dumps(
        {"type": "result", "is_error": True, "result": "You've hit your weekly limit"}
    )
    monkeypatch.setattr(
        cli.subprocess,
        "run",
        lambda *a, **kw: subprocess.CompletedProcess(a, 1, stdout=limited, stderr=""),
    )
    system = load_system("direct-cc-claude-haiku-5.5")
    task = Repository().all()[0]
    with pytest.raises(InfrastructureError, match="usage limit"):
        system.generate(task, 1)
