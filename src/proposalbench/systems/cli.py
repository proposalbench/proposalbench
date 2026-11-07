"""The ``cli`` systems: an agentic coding CLI (Codex, Claude Code) writing the proposal headless.

These are products, not bare models: each CLI brings its own system prompt and tools (file
editing, web search). They run in an empty temporary folder that holds only the system-facing
bundle (call.md, dossier/, brief.md, instructions.md) and must write proposal.md there.
Claude Code runs in restricted mode (no shell; file tools confined to the folder). Codex cannot
be sandboxed on every machine, so every run's transcript is audited: a run that mentions the
repository path or a hidden answer-key file name is discarded as contaminated.
"""

from __future__ import annotations

import contextlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

from proposalbench.llm import InfrastructureError, family_of
from proposalbench.systems.base import ModelUsage, Submission, SubmissionMeta, content_hash
from proposalbench.systems.direct import SYSTEM_PROMPT, USER_PROMPT, build_prompt
from proposalbench.tasks.loader import DATA_ROOT, ResolvedTask
from proposalbench.tasks.render_instructions import export_bundle

PROMPT = """\
The files in this folder are everything you have about this funding application: the call in \
call.md, the applicant's documents in dossier/, the applicant's notes in brief.md (if present) \
and the instructions in instructions.md. Follow instructions.md and write the complete proposal \
to a file named proposal.md in this folder. You may search the web for scientific literature. \
Do not read or list files outside this folder.
"""
# Direct (model-track) runs: Codex keeps its own system prompt, so it is told not to act.
DIRECT_NOTE = (
    "Do not run commands, read files or browse: everything you need is above. Reply with the "
    "complete proposal in Markdown only."
)
HIDDEN_NAMES = ("call.yaml", "dossier.yaml", "task.yaml")
MIN_PROPOSAL_CHARS = 1500


@dataclass
class CliSystem:
    id: str
    tool: str  # "codex" | "claude"
    model: str
    mode: str = "agent"  # "agent": tools and web; "direct": the baseline prompt, no tools
    effort: str | None = None
    timeout_s: int = 3600
    # The Codex profile folder; PB_CODEX_HOME overrides the default.
    codex_home: str = field(default_factory=lambda: os.environ.get("PB_CODEX_HOME", "~/.codex"))
    isolation: str = "none"  # "docker": run Codex in a container that sees only the bundle

    def version(self) -> str:
        prompt = PROMPT if self.mode == "agent" else SYSTEM_PROMPT + USER_PROMPT + DIRECT_NOTE
        return content_hash(
            prompt, self.tool, self.model, self.mode, str(self.effort), _tool_version(self.tool)
        )

    def _direct_command(self, folder: Path) -> list[str]:
        if self.tool == "codex":
            cmd = ["codex", "exec", "-m", self.model, "-s", "danger-full-access", "-C", str(folder)]
            cmd += [
                "--skip-git-repo-check",
                "--ephemeral",
                "--json",
                "-c",
                "tools.web_search=false",
            ]
            cmd += ["-o", str(folder / "last.md")]
            if self.effort:
                cmd += ["-c", f'model_reasoning_effort="{self.effort}"']
            return [*cmd, "-"]
        if self.tool == "claude":
            # stream-json: a long answer spans turns and "result" holds only the last one.
            cmd = ["claude", "-p", "--model", self.model, "--tools", ""]
            cmd += ["--output-format", "stream-json", "--verbose"]
            cmd += ["--system-prompt", SYSTEM_PROMPT, "--strict-mcp-config"]
            cmd += ["--no-session-persistence"]
            if self.effort:
                cmd += ["--effort", self.effort]
            return cmd
        raise ValueError(f"unknown CLI tool {self.tool!r}")

    def _command(self, folder: Path) -> list[str]:
        cmd = self._direct_command(folder) if self.mode == "direct" else self._agent_command(folder)
        if self.isolation == "docker" and self.tool == "codex":
            return _in_docker(cmd, folder, Path(os.path.expanduser(self.codex_home)))
        return cmd

    def _agent_command(self, folder: Path) -> list[str]:
        if self.tool == "codex":
            cmd = ["codex", "exec", "-m", self.model, "-s", "danger-full-access", "-C", str(folder)]
            cmd += ["--skip-git-repo-check", "--ephemeral", "--json", "-c", "tools.web_search=true"]
            if self.effort:
                cmd += ["-c", f'model_reasoning_effort="{self.effort}"']
            return [*cmd, "-"]
        if self.tool == "claude":
            cmd = ["claude", "-p", "--model", self.model, "--output-format", "json"]
            cmd += ["--restricted", "--strict-mcp-config", "--no-session-persistence"]
            cmd += ["--tools", "Read,Write,Edit,Glob,Grep,WebSearch,WebFetch"]
            cmd += ["--permission-mode", "acceptEdits", "--permission-prompts", "none"]
            if self.effort:
                cmd += ["--effort", self.effort]
            return cmd
        raise ValueError(f"unknown CLI tool {self.tool!r}")

    def generate(self, task: ResolvedTask, sample: int) -> Submission:
        usage = ModelUsage(self.model, _family(self.tool, self.model))
        meta = SubmissionMeta(
            self.id, self.version(), task.id, task.task.split.value, sample, "ok", models=[usage]
        )
        direct = self.mode == "direct"
        meta.tools = [] if direct else [f"{self.tool}-cli", "web_search", "file_edit"]
        env = os.environ.copy()
        if self.tool == "codex":
            env["CODEX_HOME"] = os.path.expanduser(self.codex_home)
        if self.tool == "claude":
            env["CLAUDE_CODE_MAX_OUTPUT_TOKENS"] = "64000"
            if direct:
                # The model track is the plain prompt: no user-level instructions or memory.
                env["CLAUDE_CODE_DISABLE_CLAUDE_MDS"] = "1"
                env["CLAUDE_CODE_DISABLE_AUTO_MEMORY"] = "1"
        if direct:
            # The baseline prompt with every file inlined; the folder stays empty.
            stdin = build_prompt(task)
            if self.tool == "codex":
                stdin = f"{SYSTEM_PROMPT}\n\n{stdin}\n{DIRECT_NOTE}"
        else:
            stdin = PROMPT
        proposal = self._attempt(task, direct, env, stdin, usage, meta, time.monotonic())
        if isinstance(proposal, Submission):
            return proposal
        if len(proposal.strip()) < MIN_PROPOSAL_CHARS:
            meta.status = "model_failure"
            meta.notes.append("no substantive proposal.md written")
        return Submission(proposal, meta)

    def _attempt(self, task, direct, env, stdin, usage, meta, start):
        """One run: the proposal text or a finished Submission."""
        with _run_folder() as folder:
            if not direct:
                export_bundle(task, folder)
            try:
                done = subprocess.run(
                    self._command(folder),
                    input=stdin,
                    text=True,
                    capture_output=True,
                    cwd=folder,
                    env=env,
                    timeout=self.timeout_s,
                )
            except subprocess.TimeoutExpired:
                meta.status = "model_failure"
                meta.notes.append(f"no result within {self.timeout_s} s")
                meta.wall_time_s = round(time.monotonic() - start, 1)
                return Submission("", meta)
            if limit := usage_limit(done.stdout, done.stderr):
                # Not a model result: the run is discarded and generated again from scratch once
                # the subscription's limit resets (`pb run` retries infrastructure failures).
                raise InfrastructureError(f"subscription usage limit: {limit[:200]}")
            meta.wall_time_s = round(time.monotonic() - start, 1)
            transcript = done.stdout + done.stderr
            output = folder / ("last.md" if direct and self.tool == "codex" else "proposal.md")
            if direct and self.tool == "claude" and done.returncode == 0:
                output.write_text(_direct_text(done.stdout), "utf-8")
            if direct and self.tool == "codex" and _ran_commands(done.stdout):
                meta.notes.append("codex executed commands despite the instruction")
            if done.returncode != 0 and not output.is_file():
                raise InfrastructureError(
                    f"{self.tool} exited {done.returncode}: {done.stderr[-300:]}"
                )
            _account(self.tool, done.stdout, usage, meta)
            if leak := _contamination(transcript):
                meta.status = "infrastructure_failure"
                meta.notes.append(f"discarded: transcript mentions {leak}")
                return Submission("", meta)
            return output.read_text(encoding="utf-8") if output.is_file() else ""


LIMIT_TEXT = re.compile(
    r"hit your [\w\s-]*limit|usage limit|limit reached|out of (extra )?usage|credit balance",
    re.IGNORECASE,
)


def usage_limit(stdout: str, stderr: str) -> str | None:
    """The limit message if a ``claude -p --output-format json`` run stopped at a usage limit."""
    for line in stdout.splitlines() or [stdout]:
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if not isinstance(event, dict) or event.get("type") != "result":
            continue
        text = str(event.get("result") or "")
        if event.get("is_error") and (
            LIMIT_TEXT.search(text) or event.get("api_error_status") == 429
        ):
            return text or "HTTP 429"
    if m := re.search(r"You've hit your[^\n]*", stderr):
        return m.group(0)
    return None


DOCKER_IMAGE = "ubuntu:24.04"


def _codex_home(folder: Path) -> Path:
    return folder.parent / f"{folder.name}-codex-home"


@contextlib.contextmanager
def _run_folder() -> Iterator[Path]:
    """A temporary folder for one run; a Docker run's private Codex home (about 90 MB, kept
    outside the folder so Codex cannot read it as task input) goes with it."""
    with tempfile.TemporaryDirectory(prefix="pb-cli-") as tmp:
        folder = Path(tmp)
        try:
            yield folder
        finally:
            shutil.rmtree(_codex_home(folder), ignore_errors=True)


def _in_docker(cmd: list[str], folder: Path, codex_home: Path) -> list[str]:
    """Run a Codex command in a container that sees only the task folder.

    The container gets the Node runtime holding the Codex CLI (read-only), the host's CA
    certificates, a private Codex home with a copy of config.toml, and the real auth.json (a
    token refresh must reach the host's credentials). Paths to the folder become /work.
    """
    script = Path(os.path.realpath(shutil.which("codex") or "codex"))
    node = script.parents[5]  # <node>/lib/node_modules/@openai/codex/bin/codex.js
    home = _codex_home(folder)
    home.mkdir(exist_ok=True)
    if (codex_home / "config.toml").is_file():
        shutil.copyfile(codex_home / "config.toml", home / "config.toml")
    (home / "auth.json").touch()
    inner = [str(node / "bin" / "node"), str(script), *cmd[1:]]
    inner = [a.replace(str(folder), "/work") for a in inner]
    return [
        "docker", "run", "--rm", "-i",
        "-u", f"{os.getuid()}:{os.getgid()}",
        "-e", "HOME=/tmp", "-e", "CODEX_HOME=/codex",
        "-v", "/etc/ssl/certs:/etc/ssl/certs:ro",
        "-v", f"{node}:{node}:ro",
        "-v", f"{home}:/codex",
        "-v", f"{codex_home / 'auth.json'}:/codex/auth.json",
        "-v", f"{folder}:/work", "-w", "/work",
        DOCKER_IMAGE, *inner,
    ]  # fmt: skip


def _direct_text(stdout: str) -> str:
    """The whole answer of a direct ``claude -p`` run, from its stream-json events.

    Claude Code continues after each hit of the output limit, so a long answer spans turns,
    which join directly. A later turn that starts the document again replaces what came
    before it, so an answer written twice is not submitted twice.
    """
    turns: list[str] = []
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if not isinstance(event, dict) or event.get("type") != "assistant":
            continue
        content = (event.get("message") or {}).get("content") or []
        text = "".join(b.get("text", "") for b in content if b.get("type") == "text")
        if text:
            turns.append(text)
    if len(turns) > 1 and (first := turns[0].lstrip().split("\n", 1)[0]).startswith("#"):
        for i in range(len(turns) - 1, 0, -1):
            if turns[i].lstrip().startswith(first):
                turns = turns[i:]
                break
    return "".join(turns)


def _ran_commands(stdout: str) -> bool:
    """Whether Codex's JSON event stream shows a command execution."""
    return '"command_execution"' in stdout or '"exec_command' in stdout


def _family(tool: str, model: str) -> str:
    try:
        return family_of(model)
    except ValueError:
        return {"codex": "openai", "claude": "anthropic"}[tool]


def _tool_version(tool: str) -> str:
    try:
        return subprocess.run([tool, "--version"], capture_output=True, text=True).stdout.strip()
    except OSError:
        return "unavailable"


def _contamination(transcript: str) -> str | None:
    repo = str(DATA_ROOT.parent)
    if repo in transcript:
        return "the repository path"
    for name in HIDDEN_NAMES:
        if name in transcript:
            return name
    return None


def _account(tool: str, stdout: str, usage: ModelUsage, meta: SubmissionMeta) -> None:
    """Token usage and cost from the CLI's JSON output (best effort)."""
    events = []
    for line in stdout.splitlines():
        try:
            events.append(json.loads(line))
        except ValueError:
            continue
    for event in events:
        if tool == "claude" and event.get("type") == "result":
            u = event.get("usage") or {}
            cached = int(u.get("cache_read_input_tokens", 0))
            usage.input_tokens += int(u.get("input_tokens", 0)) + cached
            usage.cached_input_tokens = (usage.cached_input_tokens or 0) + cached
            usage.output_tokens += int(u.get("output_tokens", 0))
            usage.calls += int(event.get("num_turns", 0))
            meta.cost_usd = event.get("total_cost_usd")
            if models := list((event.get("modelUsage") or {}).keys()):
                meta.notes.append(f"models used: {', '.join(models)}")
        elif tool == "codex":
            u = event.get("usage") or (event.get("msg") or {}).get("usage") or {}
            if isinstance(u, dict) and ("input_tokens" in u or "output_tokens" in u):
                # Codex's input_tokens already include the cache hits.
                usage.input_tokens += int(u.get("input_tokens", 0))
                usage.cached_input_tokens = (usage.cached_input_tokens or 0) + int(
                    u.get("cached_input_tokens", 0)
                )
                usage.output_tokens += int(u.get("output_tokens", 0))
                usage.calls += 1
