"""Load calls, dossiers and tasks from ``data/<split>/`` and resolve them into bundles."""

from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property
from pathlib import Path

import yaml

from proposalbench.tasks.schema import Call, Dossier, MethodProfile, Split, Task

DATA_ROOT = Path(__file__).resolve().parents[3] / "data"


def _read_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


@dataclass(frozen=True)
class ResolvedTask:
    task: Task
    call: Call
    dossier: Dossier
    task_dir: Path
    call_dir: Path
    dossier_dir: Path

    @property
    def id(self) -> str:
        return self.task.id

    @property
    def method_profile(self) -> MethodProfile:
        return self.task.method_profile or self.dossier.method_profile

    @cached_property
    def call_text(self) -> str:
        return (self.call_dir / "call.md").read_text(encoding="utf-8")

    def dossier_texts(self) -> dict[str, str]:
        return {
            f.path: (self.dossier_dir / f.path).read_text(encoding="utf-8")
            for f in self.dossier.files
        }

    @cached_property
    def brief_text(self) -> str | None:
        if not self.task.brief:
            return None
        return (self.task_dir / self.task.brief).read_text(encoding="utf-8")


class Repository:
    """All calls, dossiers and tasks of one or more splits."""

    def __init__(self, root: Path = DATA_ROOT):
        self.root = root

    def splits(self) -> list[Split]:
        return [s for s in Split if (self.root / s.value).is_dir()]

    def load_call(self, split: Split, call_id: str) -> tuple[Call, Path]:
        d = self.root / split.value / "calls" / call_id
        return Call.model_validate(_read_yaml(d / "call.yaml")), d

    def load_dossier(self, split: Split, dossier_id: str) -> tuple[Dossier, Path]:
        d = self.root / split.value / "dossiers" / dossier_id
        return Dossier.model_validate(_read_yaml(d / "dossier.yaml")), d

    def task_dirs(self, split: Split | None = None) -> list[Path]:
        splits = [split] if split else self.splits()
        out: list[Path] = []
        for s in splits:
            tasks = self.root / s.value / "tasks"
            if tasks.is_dir():
                out.extend(sorted(p for p in tasks.iterdir() if (p / "task.yaml").is_file()))
        return out

    def load_task(self, task_dir: Path) -> ResolvedTask:
        task_data = _read_yaml(task_dir / "task.yaml")
        task = Task.model_validate(task_data)
        if task_dir.parent.parent.name != task.split.value:
            raise ValueError(f"{task.id}: declared split {task.split} but stored under {task_dir}")
        call, call_dir = self.load_call(task.split, task.call_id)
        dossier, dossier_dir = self.load_dossier(task.split, task.dossier_id)
        task = Task.model_validate(task_data, context={"call": call, "dossier": dossier})
        return ResolvedTask(task, call, dossier, task_dir, call_dir, dossier_dir)

    def get(self, task_id: str) -> ResolvedTask:
        for d in self.task_dirs():
            if d.name == task_id:
                return self.load_task(d)
        raise KeyError(f"unknown task {task_id!r}")

    def all(self, split: Split | None = None) -> list[ResolvedTask]:
        return [self.load_task(d) for d in self.task_dirs(split)]
