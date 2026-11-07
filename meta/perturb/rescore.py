"""Re-evaluate an existing perturbation folder after an evaluator change.

    uv run python -m meta.perturb.rescore --out results/meta/perturb-v1a [--operators ...]

Every evaluation stage whose output exists is reused (see evaluate.py), so only stages that are
new or invalidated run. Detection is recomputed for every pair and the summary is rewritten.
Re-score the base evaluations first (`pb evaluate`) when an operator's control is the base.
"""

from __future__ import annotations

import argparse
import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path

from meta.perturb.operators import Expectation
from meta.perturb.run import _write, detect, summarize
from proposalbench.systems.base import Submission, SubmissionMeta
from proposalbench.tasks.loader import Repository


def rescore(out: Path, operators: list[str] | None, panel: str, workers: int) -> dict:
    from proposalbench.evaluate import evaluate_submission, load_panel

    specs = load_panel(panel)[1] if panel != "none" else []
    repo = Repository()
    tasks = {d.name: d for d in repo.task_dirs()}
    pairs = []
    for path in sorted(out.glob("*/*/*/*/expectation.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        if not record.get("applicable") or (operators and record["operator"] not in operators):
            continue
        pairs.append((path.parent, record))

    def one(item):
        folder, record = item
        expectation = Expectation.from_dict(record["expectation"])
        rt = repo.load_task(tasks[record["task"]])
        meta = SubmissionMeta.from_json(Path(record["base_meta"]).read_text(encoding="utf-8"))
        judged = any(d.family != "deterministic" for d in expectation.detectors)
        for variant in ("perturbed", "control"):
            if variant == "control" and expectation.control_is_base:
                continue
            destination = folder / "evaluation" / variant
            if not destination.is_dir():
                continue
            text = (folder / f"{variant}.md").read_text(encoding="utf-8")
            suffix = "perturb" if variant == "perturbed" else "control"
            copied = replace(meta, system_id=f"{meta.system_id}+{suffix}:{expectation.operator}")
            evaluate_submission(
                rt,
                Submission(text, copied),
                destination,
                specs if judged else [],
                out / "evidence-cache.sqlite",
            )
        base = Path(record["base"]).parent
        control = base if expectation.control_is_base else folder / "evaluation/control"
        _write(
            folder / "detection.json",
            detect(expectation, folder / "evaluation/perturbed", control, base, rt),
        )

    with ThreadPoolExecutor(max_workers=workers) as pool:
        list(pool.map(one, pairs))
    return summarize(out)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--operators", nargs="+")
    parser.add_argument(
        "--panel", default="panel-pilot", help="Judge panel, or none for deterministic stages only."
    )
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    rescore(args.out, args.operators, args.panel, args.workers)
    print((args.out / "summary.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
