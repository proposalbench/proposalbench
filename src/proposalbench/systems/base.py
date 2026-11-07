"""System interface and the on-disk submission format.

A submission is ``submissions/<system_id>/<split>/<task_id>/<sample>/`` with ``proposal.md``
and ``meta.json``. Closed systems, commercial tools and humans submit in the same format.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal, Protocol

from proposalbench.tasks.loader import ResolvedTask

SUBMISSIONS = Path(__file__).resolve().parents[3] / "submissions"

Status = Literal["ok", "model_failure", "infrastructure_failure"]


@dataclass
class ModelUsage:
    model_id: str
    family: str
    calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    # The part of input_tokens served from a prompt cache; None where it was not recorded.
    cached_input_tokens: int | None = None


@dataclass
class SubmissionMeta:
    system_id: str
    system_version: str
    task_id: str
    split: str
    sample: int
    status: Status
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat(timespec="seconds"))
    models: list[ModelUsage] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)
    human_intervention: Literal["none", "light_edit", "heavy_edit"] = "none"
    wall_time_s: float | None = None
    cost_usd: float | None = None
    retries: list[dict] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    logs_available: bool = True
    # Hash of the files the system received (``task_version``); a task edited after generation
    # makes the submission stale.
    task_version: str | None = None

    @property
    def families(self) -> set[str]:
        return {m.family for m in self.models}

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, ensure_ascii=False)

    @classmethod
    def from_json(cls, text: str) -> SubmissionMeta:
        data = json.loads(text)
        data["models"] = [ModelUsage(**m) for m in data.get("models", [])]
        return cls(**data)


@dataclass
class Submission:
    proposal: str
    meta: SubmissionMeta


class System(Protocol):
    id: str

    def version(self) -> str: ...

    def generate(self, task: ResolvedTask, sample: int) -> Submission: ...


def submission_dir(system_id: str, task: ResolvedTask, sample: int, root: Path = SUBMISSIONS):
    return root / system_id / task.task.split.value / task.id / str(sample)


def save(sub: Submission, directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "proposal.md").write_text(sub.proposal, encoding="utf-8")
    (directory / "meta.json").write_text(sub.meta.to_json(), encoding="utf-8")


def load(directory: Path) -> Submission:
    return Submission(
        (directory / "proposal.md").read_text(encoding="utf-8"),
        SubmissionMeta.from_json((directory / "meta.json").read_text(encoding="utf-8")),
    )


def task_version(task: ResolvedTask) -> str:
    """Hash of exactly what a system receives for TASK (the exported bundle)."""
    import tempfile

    from proposalbench.tasks.render_instructions import export_bundle

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        export_bundle(task, root)
        h = hashlib.sha256()
        for p in sorted(p for p in root.rglob("*") if p.is_file()):
            h.update(f"{p.relative_to(root)}\0".encode() + p.read_bytes() + b"\0")
        return h.hexdigest()[:12]


def content_hash(*parts: str) -> str:
    h = hashlib.sha256()
    for p in parts:
        h.update(p.encode())
    return h.hexdigest()[:12]
