"""Author models for task synthesis: Bedrock and Google through proposalbench.llm, OpenAI
through the Codex CLI (no working OpenAI API key; GPT models are reached headless), and current
Claude models through Claude Code in print mode with tools disabled.

The Codex route runs ``codex exec`` in an empty scratch directory and is told to reply with
text only. ``PB_CODEX_HOME`` selects the Codex profile (default ``~/.codex``).
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from proposalbench.llm import ModelSpec, complete

CODEX_TIMEOUT_S = 3600


@dataclass(frozen=True)
class Author:
    family: str
    provider: str  # "bedrock" | "google" | "codex"
    model: str

    @classmethod
    def from_matrix(cls, family: str, cfg: dict) -> Author:
        return cls(family, cfg["provider"], cfg["model"])


def _codex(model: str, system: str, prompt: str) -> str:
    home = os.environ.get("PB_CODEX_HOME", str(Path.home() / ".codex"))
    with tempfile.TemporaryDirectory(prefix="pb-author-") as tmp:
        out = Path(tmp) / "last.md"
        task = (
            f"{system}\n\n{prompt}\n\n"
            "Do not run commands, read files or browse; answer from your own knowledge. "
            "Reply with the requested output only."
        )
        subprocess.run(
            [
                "codex",
                "exec",
                "-m",
                model,
                "-c",
                'model_reasoning_effort="high"',
                "-s",
                "danger-full-access",
                "-C",
                tmp,
                "--skip-git-repo-check",
                "--ephemeral",
                "-o",
                str(out),
                "-",
            ],
            input=task,
            text=True,
            capture_output=True,
            env=os.environ | {"CODEX_HOME": home},
            timeout=CODEX_TIMEOUT_S,
            check=True,
        )
        return out.read_text(encoding="utf-8")


def _claude(model: str, system: str, prompt: str) -> str:
    """One tool-free model call through Claude Code in print mode (no session, no MCP)."""
    with tempfile.TemporaryDirectory(prefix="pb-author-") as tmp:
        done = subprocess.run(
            [
                "claude",
                "-p",
                "--model",
                model,
                "--tools",
                "",
                "--system-prompt",
                system,
                "--output-format",
                "json",
                "--strict-mcp-config",
                "--no-session-persistence",
            ],
            input=prompt,
            text=True,
            capture_output=True,
            cwd=tmp,
            env=os.environ | {"CLAUDE_CODE_MAX_OUTPUT_TOKENS": "64000"},
            timeout=CODEX_TIMEOUT_S,
            check=True,
        )
    result = json.loads(done.stdout)
    if result.get("is_error"):
        raise RuntimeError(f"claude -p failed: {str(result.get('result'))[:300]}")
    return result["result"]


def author_complete(author: Author, system: str, prompt: str, max_tokens: int = 32000) -> str:
    if author.provider == "codex":
        return _codex(author.model, system, prompt)
    if author.provider == "claude":
        return _claude(author.model, system, prompt)
    spec = ModelSpec(author.provider, author.model, max_output_tokens=max_tokens)  # type: ignore[arg-type]
    result = complete(spec, [{"role": "user", "content": prompt}], system=system)
    if result.truncated:
        raise RuntimeError(f"{author.model} reply truncated at {max_tokens} tokens")
    return result.text
