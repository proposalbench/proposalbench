"""Aggregate evaluated samples into a per-system table.

Uncertainty is a two-way cluster bootstrap: calls and dossiers are resampled independently and a
sample is kept when both its call and its dossier are drawn, which respects the fact that tasks
share calls and dossiers.
"""

from __future__ import annotations

import json
import statistics
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from proposalbench.report import costs
from proposalbench.systems.base import SUBMISSIONS
from proposalbench.tasks.loader import Repository


@dataclass
class Row:
    system: str
    samples: int
    score: float
    ci_low: float
    ci_high: float
    quality: float | None
    components: dict[str, float | None]
    admissible: float
    critical_share: float
    words_vs_limit: float
    refs_verified: float
    refs_not_found: float
    # Diagnostics, reported and not scored (docs/scoring_spec.md): medians per proposal.
    gen_minutes: float | None = None
    gen_cost: float | None = None
    gen_cost_basis: str | None = None  # see report.costs
    subscription: bool = False  # run on a subscription; the cost is the API equivalent
    judge_cost: float | None = None
    judge_cost_basis: str | None = None  # "measured" | "run_average"


def load_scores(results_dir: Path) -> list[dict]:
    return [json.loads(p.read_text()) for p in sorted(results_dir.glob("*/*/*/*/score.json"))]


def _scored_samples(results_dir: Path) -> list[tuple[Path, dict]]:
    return [
        (p.parent, json.loads(p.read_text()))
        for p in sorted(results_dir.glob("*/*/*/*/score.json"))
    ]


def _median(xs: list[float]) -> float | None:
    return round(statistics.median(xs), 2) if xs else None


def _diagnostics(
    system: str,
    dirs: list[Path],
    results_dir: Path,
    submissions_dir: Path,
    prices: dict[str, costs.Price],
    run_judging: dict | None,
) -> dict:
    """Time, generation cost and judging cost for one system's scored samples."""
    kind, tool = costs.system_tool(system)
    minutes, gen, bases, judged = [], [], [], []
    for d in dirs:
        meta_path = submissions_dir / d.relative_to(results_dir) / "meta.json"
        if meta_path.exists():
            meta = json.loads(meta_path.read_text())
            if meta.get("wall_time_s"):
                minutes.append(meta["wall_time_s"] / 60)
            c = costs.generation_cost(meta, prices, tool)
            if c.usd is not None:
                gen.append(c.usd)
                bases.append(c.basis)
        if (j := costs.judging_cost(d, prices)) is not None:
            judged.append(j)
    if judged and len(judged) == len(dirs):
        judge_cost, judge_basis = _median(judged), "measured"
    elif run_judging:
        judge_cost, judge_basis = round(run_judging["per_evaluation_usd"], 2), "run_average"
    else:
        judge_cost, judge_basis = None, None
    return {
        "gen_minutes": round(statistics.median(minutes), 1) if minutes else None,
        "gen_cost": _median(gen),
        "gen_cost_basis": costs.weakest(bases),
        "subscription": kind == "cli",
        "judge_cost": judge_cost,
        "judge_cost_basis": judge_basis,
    }


def cluster_bootstrap(
    scores: list[float],
    calls: list[str],
    dossiers: list[str],
    n: int = 2000,
    seed: int = 0,
    tasks: list[str] | None = None,
) -> tuple[float, float]:
    """Two-way (calls x dossiers) bootstrap; with ``tasks``, samples within each task are also
    resampled, so sample-to-sample noise of a system enters the interval."""
    rng = np.random.default_rng(seed)
    call_ids, dossier_ids = sorted(set(calls)), sorted(set(dossiers))
    s = np.array(scores, dtype=float)
    ci = np.array([call_ids.index(c) for c in calls])
    di = np.array([dossier_ids.index(d) for d in dossiers])
    groups: list[np.ndarray] = []
    if tasks is not None:
        for t in sorted(set(tasks)):
            groups.append(np.array([i for i, x in enumerate(tasks) if x == t]))
    means = []
    for _ in range(n):
        wc = np.bincount(rng.integers(0, len(call_ids), len(call_ids)), minlength=len(call_ids))
        wd = np.bincount(
            rng.integers(0, len(dossier_ids), len(dossier_ids)), minlength=len(dossier_ids)
        )
        w = (wc[ci] * wd[di]).astype(float)
        if groups:
            within = np.zeros(len(s))
            for g in groups:
                within[g] = np.bincount(rng.integers(0, len(g), len(g)), minlength=len(g))
            w = w * within
        if w.sum() > 0:
            means.append(float((w * s).sum() / w.sum()))
    lo, hi = np.percentile(means, [2.5, 97.5])
    return round(float(lo), 2), round(float(hi), 2)


def _mean(xs: list[float | None]) -> float | None:
    vals = [x for x in xs if x is not None]
    return round(sum(vals) / len(vals), 2) if vals else None


def leaderboard(
    results_dir: Path,
    submissions_dir: Path = SUBMISSIONS,
    select: Callable[[dict], bool] | None = None,
) -> list[Row]:
    """One row per system; ``select`` keeps only the scored samples (score dicts) it accepts."""
    repo = Repository()
    prices = costs.load_prices()
    run_judging = costs.run_judging_cost(results_dir)
    by_system: dict[str, list[dict]] = defaultdict(list)
    dirs_by_system: dict[str, list[Path]] = defaultdict(list)
    for d, s in _scored_samples(results_dir):
        if select is not None and not select(s):
            continue
        by_system[s["system"]].append(s)
        dirs_by_system[s["system"]].append(d)
    rows = []
    for system, samples in sorted(by_system.items()):
        tasks = {s["task"]: repo.get(s["task"]) for s in samples}
        scores = [s["scorecard"]["score"] for s in samples]
        calls = [tasks[s["task"]].call.id for s in samples]
        dossiers = [tasks[s["task"]].dossier.id for s in samples]
        lo, hi = cluster_bootstrap(scores, calls, dossiers, tasks=[s["task"] for s in samples])
        comps = {
            c: _mean([s["scorecard"]["components"].get(c) for s in samples])
            for c in ("call_responsiveness", "substance", "grounding")
        }
        ratio = [
            s["counted_words"] / tasks[s["task"]].call.length_contract.max_words for s in samples
        ]
        refs_total = [max(1, sum(s["references"].values())) for s in samples]
        verified = [
            (s["references"].get("verified", 0) + s["references"].get("verified_with_errors", 0))
            / t
            for s, t in zip(samples, refs_total, strict=True)
        ]
        not_found = [
            s["references"].get("not_found", 0) / t
            for s, t in zip(samples, refs_total, strict=True)
        ]
        rows.append(
            Row(
                system=system,
                samples=len(samples),
                score=round(sum(scores) / len(scores), 2),
                ci_low=lo,
                ci_high=hi,
                quality=_mean([s["scorecard"]["quality"] for s in samples]),
                components=comps,
                admissible=round(
                    sum(s["scorecard"]["admissible"] for s in samples) / len(samples), 2
                ),
                critical_share=round(
                    sum(s["scorecard"]["has_critical"] for s in samples) / len(samples), 2
                ),
                words_vs_limit=round(sum(ratio) / len(ratio), 2),
                refs_verified=round(sum(verified) / len(verified), 2),
                refs_not_found=round(sum(not_found) / len(not_found), 2),
                **_diagnostics(
                    system,
                    dirs_by_system[system],
                    results_dir,
                    submissions_dir,
                    prices,
                    run_judging,
                ),
            )
        )
    return sorted(rows, key=lambda r: -r.score)


def _usd(value: float | None, basis: str | None, subscription: bool = False) -> str:
    if value is None:
        return "—"
    text = f"${value:.2f}"
    if basis == "upper_bound":
        text = "≤" + text + " est."
    elif basis in ("estimated", "run_average"):
        text += " est." if basis == "estimated" else " avg"
    return text + (" †" if subscription else "")


def to_markdown(rows: list[Row]) -> str:
    head = (
        "| System | n | Score [95% CI] | Quality | Call | Substance | Grounding | Admissible | "
        "≥1 critical | Words/limit | Refs verified | Refs not found | Time (min) | "
        "Generation cost | Judging cost |\n"
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"
    )
    lines = [head]
    for r in rows:
        c = r.components
        minutes = "—" if r.gen_minutes is None else f"{r.gen_minutes:.1f}"
        lines.append(
            f"| {r.system} | {r.samples} | {r.score} [{r.ci_low}, {r.ci_high}] | {r.quality} | "
            f"{c['call_responsiveness']} | {c['substance']} | {c['grounding']} | "
            f"{r.admissible:.0%} | {r.critical_share:.0%} | {r.words_vs_limit:.2f} | "
            f"{r.refs_verified:.0%} | {r.refs_not_found:.0%} | {minutes} | "
            f"{_usd(r.gen_cost, r.gen_cost_basis, r.subscription)} | "
            f"{_usd(r.judge_cost, r.judge_cost_basis)} |"
        )
    lines += [
        "",
        "Time and costs are medians per proposal, reported and not scored. Generation cost is the "
        "system's own figure where it records one; *est.* is recorded tokens × "
        "`configs/prices.yaml`; *≤ … est.* prices cache hits as uncached input (an upper bound); "
        "† ran on a subscription, so the figure is the API equivalent. Judging cost *avg* is a "
        "run-level average from the cloud bill, for runs judged before token recording.",
    ]
    return "\n".join(lines)
