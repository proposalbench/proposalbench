"""Proposia (commercial participant), run from a pinned checkout with production settings.

Proposia takes what its web app takes: one prior-research file, one call file and free-text
notes. The task maps onto those inputs as a user would: the dossier files are merged into one
Markdown file (each under its file name), call.md is the call, and the notes hold the brief
followed by the instructions every system receives. The driver named in the config (in
``tools/proposia/``) runs the workflow inside the checkout with Proposia's own interpreter and
keys, without database access.
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path

from proposalbench.llm import InfrastructureError
from proposalbench.systems.base import ModelUsage, Submission, SubmissionMeta, content_hash
from proposalbench.tasks.loader import ResolvedTask
from proposalbench.tasks.render_instructions import export_bundle

TOOLS = Path(__file__).resolve().parents[3] / "tools" / "proposia"
WORK_ROOT = Path(__file__).resolve().parents[3] / ".work" / "proposia-runs"
MIN_PROPOSAL_CHARS = 1500


def _path(value: str) -> str:
    """A config path: environment variables (e.g. ``${PROPOSIA_CHECKOUT}``) and ``~`` expanded."""
    return os.path.expanduser(os.path.expandvars(value))


def merged_dossier(bundle: Path) -> str:
    parts = ["# Applicant documents\n"]
    for f in sorted((bundle / "dossier").rglob("*")):
        if f.is_file():
            rel = f.relative_to(bundle / "dossier")
            parts.append(f"\n\n# File: {rel}\n\n{f.read_text(encoding='utf-8').strip()}\n")
    return "".join(parts)


def notes(bundle: Path) -> str:
    out = []
    if (bundle / "brief.md").is_file():
        brief = (bundle / "brief.md").read_text(encoding="utf-8").strip()
        out.append(f"Applicant's notes:\n\n{brief}")
    instructions = (bundle / "instructions.md").read_text(encoding="utf-8").strip()
    out.append(f"Submission instructions:\n\n{instructions}")
    return "\n\n".join(out) + "\n"


@dataclass
class ProposiaSystem:
    id: str
    checkout: str  # git worktree at the pinned commit
    commit: str | None  # None: development checkout, recorded as HEAD plus its uncommitted diff
    python: str  # Proposia's virtualenv interpreter
    families: list[str] = field(default_factory=lambda: ["google", "anthropic", "qwen"])
    timeout_s: int = 7200
    driver: str = "driver_v2.py"
    keep_work: bool = False  # keep each run's intermediate files under .work/proposia-runs/
    env: dict[str, str] = field(default_factory=dict)

    def _driver(self) -> Path:
        return TOOLS / self.driver

    def _state(self) -> str:
        checkout = Path(_path(self.checkout))
        git = ["git", "-C", str(checkout)]
        head = subprocess.run([*git, "rev-parse", "HEAD"], capture_output=True, text=True).stdout
        diff = subprocess.run([*git, "diff", "HEAD"], capture_output=True, text=True).stdout
        new = subprocess.run(
            [*git, "ls-files", "--others", "--exclude-standard"], capture_output=True, text=True
        ).stdout.split()
        diff += "".join(f + (checkout / f).read_text("utf-8", "replace") for f in sorted(new))
        return head.strip() + ("+" + content_hash(diff) if diff else "")

    def version(self) -> str:
        pin = self.commit or self._state()
        return content_hash(pin, self._driver().read_text("utf-8"), Path(__file__).read_text())

    def generate(self, task: ResolvedTask, sample: int) -> Submission:
        models = [ModelUsage(f"proposia-pro ({fam})", fam) for fam in self.families]
        meta = SubmissionMeta(
            self.id, self.version(), task.id, task.task.split.value, sample, "ok", models=models
        )
        meta.tools = ["proposia-pro-workflow"]
        checkout = Path(_path(self.checkout))
        head = subprocess.run(
            ["git", "-C", str(checkout), "rev-parse", "HEAD"], capture_output=True, text=True
        ).stdout.strip()
        if self.commit and head != self.commit:
            raise InfrastructureError(f"Proposia checkout is at {head}, not {self.commit}")
        if not self.commit:
            meta.notes.append(f"development checkout {self._state()}")
        start = time.monotonic()
        with tempfile.TemporaryDirectory(prefix="pb-proposia-") as tmp:
            folder = Path(tmp)
            bundle = folder / "bundle"
            export_bundle(task, bundle)
            prp, cfp, note = folder / "prior_research.md", folder / "call.md", folder / "notes.md"
            prp.write_text(merged_dossier(bundle), encoding="utf-8")
            cfp.write_text((bundle / "call.md").read_text(encoding="utf-8"), encoding="utf-8")
            note.write_text(notes(bundle), encoding="utf-8")
            out = folder / "result.json"
            cmd = [_path(self.python), str(self._driver())]
            cmd += ["--prp", str(prp), "--cfp", str(cfp), "--notes", str(note)]
            cmd += ["--work", str(folder / "work"), "--out", str(out)]
            env = os.environ.copy() | {k: os.path.expandvars(str(v)) for k, v in self.env.items()}
            env.pop("VIRTUAL_ENV", None)
            try:
                done = subprocess.run(
                    cmd,
                    cwd=checkout,
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout_s,
                )
            except subprocess.TimeoutExpired:
                meta.status = "model_failure"
                meta.notes.append(f"no result within {self.timeout_s} s")
                meta.wall_time_s = round(time.monotonic() - start, 1)
                return Submission("", meta)
            meta.wall_time_s = round(time.monotonic() - start, 1)
            if not out.is_file():
                raise InfrastructureError(
                    f"Proposia exited {done.returncode}: {done.stderr[-600:]}"
                )
            result = json.loads(out.read_text(encoding="utf-8"))
            if self.keep_work:
                import shutil

                dest = WORK_ROOT / self.id / task.id / str(sample)
                shutil.rmtree(dest, ignore_errors=True)
                shutil.copytree(folder, dest, ignore=shutil.ignore_patterns("bundle"))
        proposal = result.get("proposal") or ""
        meta.notes.append(f"proposal taken from {result.get('source')}")
        summary = result.get("summary") or {}
        if isinstance(summary, dict) and summary.get("total_cost") is not None:
            meta.cost_usd = summary["total_cost"]
        if len(proposal.strip()) < MIN_PROPOSAL_CHARS:
            meta.status = "model_failure"
            meta.notes.append("no substantive proposal returned")
        return Submission(proposal, meta)
