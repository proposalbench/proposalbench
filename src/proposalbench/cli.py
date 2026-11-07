from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from proposalbench.tasks.loader import DATA_ROOT, Repository
from proposalbench.tasks.render_instructions import export_bundle
from proposalbench.tasks.schema import Split

app = typer.Typer(no_args_is_help=True, help="ProposalBench command line.")
tasks_app = typer.Typer(no_args_is_help=True, help="Inspect, validate and export tasks.")
app.add_typer(tasks_app, name="tasks")

SEEDS_RAW = DATA_ROOT.parent / "seeds_raw"


@tasks_app.command("list")
def tasks_list(split: Split | None = None) -> None:
    for rt in Repository().all(split):
        lc = rt.call.length_contract
        typer.echo(
            f"{rt.id:40} {rt.task.split:7} {rt.call.scheme:12} {rt.call.language} "
            f"{rt.task.fit_level:8} {lc.max_words:>6} words  {rt.dossier.id}"
        )


@tasks_app.command("validate")
def tasks_validate(
    seeds: Annotated[
        bool, typer.Option(help="Check n-gram overlap against seeds_raw/ if present.")
    ] = True,
) -> None:
    from proposalbench.tasks.validate import validate_repository

    problems = validate_repository(Repository(), SEEDS_RAW if seeds else None)
    errors = [p for p in problems if p.severity == "error"]
    for p in problems:
        typer.echo(f"{p.severity.upper():7} {p.where}: {p.message}")
    n = len(Repository().task_dirs())
    typer.echo(f"{n} tasks, {len(errors)} errors, {len(problems) - len(errors)} warnings")
    raise typer.Exit(1 if errors else 0)


@tasks_app.command("export")
def tasks_export(task_id: str, out: Annotated[Path, typer.Option(help="Output folder.")]) -> None:
    """Write exactly what a system receives for TASK_ID."""
    paths = export_bundle(Repository().get(task_id), out)
    typer.echo(json.dumps([str(p) for p in paths], indent=2))


@app.command("run")
def run(
    system: Annotated[str, typer.Option(help="System id in configs/systems/ or a YAML path.")],
    split: Annotated[Split | None, typer.Option(help="Restrict to one split.")] = None,
    task: Annotated[list[str] | None, typer.Option(help="Restrict to task ids.")] = None,
    samples: Annotated[int, typer.Option(help="Samples per task.")] = 2,
    workers: Annotated[int, typer.Option(help="Concurrent generations.")] = 4,
    eval_id: Annotated[
        str, typer.Option(help="Results folder for the agent evidence cache.")
    ] = "pilot",
    agent_cache: Annotated[
        Path | None, typer.Option(help="Override agent evidence cache path.")
    ] = None,
    max_usd: Annotated[
        float | None,
        typer.Option(help="Stop starting generations once recorded cost could pass this cap."),
    ] = None,
    est_usd: Annotated[
        float, typer.Option(help="Cost reserved per running generation under --max-usd.")
    ] = 6.0,
) -> None:
    """Generate proposals; existing successful samples are kept, not regenerated."""

    from proposalbench.systems.agent import ReferenceAgent
    from proposalbench.systems.base import load, save, submission_dir, task_version
    from proposalbench.systems.registry import load_system

    sys_ = load_system(system)
    if isinstance(sys_, ReferenceAgent):
        sys_.cache_path = (
            agent_cache
            or sys_.cache_path
            or DATA_ROOT.parent / "results" / eval_id / "agent-cache.sqlite"
        )
    tasks = [t for t in Repository().all(split) if not task or t.id in task]
    versions = {t.id: task_version(t) for t in tasks}
    jobs = []
    for t in tasks:
        for k in range(1, samples + 1):
            d = submission_dir(sys_.id, t, k)
            if (d / "meta.json").is_file():
                old = load(d).meta
                stale = old.task_version not in (None, versions[t.id])
                if old.status != "infrastructure_failure" and not stale:
                    continue
            jobs.append((t, k, d))
    typer.echo(f"{sys_.id}: {len(jobs)} generations to run")

    def one(t, k, d):
        try:
            sub = sys_.generate(t, k)
        except Exception as exc:
            from proposalbench.systems.base import Submission, SubmissionMeta

            meta = SubmissionMeta(
                sys_.id,
                sys_.version(),
                t.id,
                t.task.split.value,
                k,
                "infrastructure_failure",
                notes=[f"{type(exc).__name__}: {exc}"],
            )
            sub = getattr(exc, "submission", None) or Submission("", meta)
        sub.meta.task_version = versions[t.id]
        save(sub, d)
        return t.id, k, sub.meta

    def report(tid, k, meta):
        m = meta.models[0] if meta.models else None
        cost = "" if meta.cost_usd is None else f"  ${meta.cost_usd:.2f}"
        typer.echo(
            f"{tid} #{k}: {meta.status}  {meta.wall_time_s}s{cost}  "
            f"out_tokens={m.output_tokens if m else 0}  {'; '.join(meta.notes)[:120]}"
        )

    try:
        spent, left = run_capped(jobs, one, workers, max_usd, est_usd, report)
        if max_usd is not None:
            typer.echo(f"recorded cost ${spent:.2f} (cap ${max_usd:.2f}); {left} not started")
    finally:
        if isinstance(sys_, ReferenceAgent):
            sys_.close()


def run_capped(
    jobs, one, workers, max_usd, est_usd, report, cost=lambda r: r[2].cost_usd
) -> tuple[float, int]:
    """Run ``one(*job)`` with up to ``workers`` at a time and pass each result to ``report(*r)``.
    With ``max_usd``, a job starts only if the recorded cost so far plus ``est_usd`` for it and for
    each running job stays within the cap (a result whose ``cost(r)`` is None counts ``est_usd``).

    Returns (recorded cost, jobs not started)."""
    from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait

    pending, running, spent = list(jobs), set(), 0.0

    def fits() -> bool:
        return max_usd is None or spent + (len(running) + 1) * est_usd <= max_usd

    with ThreadPoolExecutor(max_workers=workers) as pool:
        while pending or running:
            while pending and len(running) < workers and fits():
                running.add(pool.submit(one, *pending.pop(0)))
            if not running:
                break
            done, running = wait(running, return_when=FIRST_COMPLETED)
            for f in done:
                r = f.result()
                c = cost(r)
                spent += est_usd if c is None else c
                report(*r)
    return spent, len(pending)


@app.command("evaluate")
def evaluate(
    system: Annotated[str, typer.Option(help="System id (folder under submissions/).")],
    panel: Annotated[str, typer.Option(help="Judge panel in configs/judges/.")] = "panel-pilot",
    eval_id: Annotated[str, typer.Option(help="Results folder name.")] = "pilot",
    split: Annotated[Split | None, typer.Option()] = None,
    offline: Annotated[bool, typer.Option(help="Replay from stored outputs only.")] = False,
    workers: Annotated[int, typer.Option(help="Submissions evaluated in parallel.")] = 2,
    max_usd: Annotated[
        float | None,
        typer.Option(
            help="Stop starting evaluations once measured judge spend could pass this cap."
        ),
    ] = None,
    est_usd: Annotated[
        float, typer.Option(help="Judge spend reserved per running evaluation under --max-usd.")
    ] = 6.0,
) -> None:
    """Evaluate every submission of SYSTEM and print one line per sample."""
    from proposalbench.evaluate import (
        RESULTS,
        SourceUnavailable,
        evaluate_submission,
        load_panel,
    )
    from proposalbench.llm import family_of
    from proposalbench.report.costs import judging_cost, load_prices
    from proposalbench.systems.base import SUBMISSIONS, load

    _, specs = load_panel(panel)
    prices = load_prices()
    repo = Repository()
    jobs = []
    retry_later = 0
    for meta_path in sorted((SUBMISSIONS / system).glob("*/*/*/meta.json")):
        d = meta_path.parent
        sub = load(d)
        if split and sub.meta.split != split.value:
            continue
        if sub.meta.status == "infrastructure_failure":
            # Not a system result: the run failed on our side and is generated again.
            retry_later += 1
            continue
        clash = {family_of(s.model_id) for s in specs} & sub.meta.families
        if clash:
            raise typer.BadParameter(f"judge family overlaps the system: {sorted(clash)}")
        out = RESULTS / eval_id / system / sub.meta.split / sub.meta.task_id / str(sub.meta.sample)
        jobs.append((repo.get(sub.meta.task_id), sub, out))
    cache = RESULTS / eval_id / "evidence-cache.sqlite"

    def one(rt, sub, out):
        before = judging_cost(out, prices) if out.is_dir() else 0.0
        try:
            s = evaluate_submission(rt, sub, out, specs, cache, offline=offline)
        except SourceUnavailable as exc:
            return {"deferred": f"{sub.meta.task_id} #{sub.meta.sample}: {exc}"}, None
        except Exception as exc:
            # One failed evaluation (an expired AWS signature, a dropped connection) must not
            # end the pass: stored stages are reused when the next pass reaches it.
            return {"deferred": f"{sub.meta.task_id} #{sub.meta.sample}: {exc!r}"[:300]}, None
        return s, new_spend(before, judging_cost(out, prices))

    def report(s, spend):
        if "deferred" in s:
            typer.echo(s["deferred"])
            return
        c = s["scorecard"]
        comps = " ".join(f"{k[:4]}={v}" for k, v in c["components"].items())
        cost = "" if spend is None else f" judges=${spend:.2f}"
        typer.echo(
            f"{s['task']:30} #{s['sample']} score={c['score']:6.2f} quality={c['quality']} "
            f"ded={c['deductions']} {comps} refs={s['references']}{cost}"
        )

    if retry_later:
        typer.echo(f"{retry_later} infrastructure failures not evaluated (run them again)")
    spent, left = run_capped(jobs, one, workers, max_usd, est_usd, report, cost=lambda r: r[1])
    if max_usd is not None:
        typer.echo(f"measured judge spend ${spent:.2f} (cap ${max_usd:.2f}); {left} not started")


def new_spend(before: float | None, after: float | None) -> float | None:
    """Judge spend added by one evaluation pass; None (counted as the estimate) when it can't be
    measured. Stages already stored before the pass cost nothing again."""
    if after is None:
        return None
    return round(max(0.0, after - (before or 0.0)), 4)


@app.command("report")
def report(eval_id: Annotated[str, typer.Option(help="Results folder name.")] = "pilot") -> None:
    """Per-system table with two-way cluster-bootstrap intervals."""
    from proposalbench.evaluate import RESULTS
    from proposalbench.report.leaderboard import leaderboard, to_markdown

    typer.echo(to_markdown(leaderboard(RESULTS / eval_id)))


@app.command("export")
def export(
    release: Annotated[str, typer.Option(help="Release config in configs/release/ or a path.")],
    out: Annotated[Path | None, typer.Option(help="Output folder.")] = None,
    explorer: Annotated[
        Path | None, typer.Option(help="Also write the proposal explorer files here.")
    ] = None,
) -> None:
    """Write a release's numbers: release.json, samples.csv and numbers.tex."""
    from proposalbench.evaluate import RESULTS
    from proposalbench.report.export import Release, build, leaderboard_md, update_readme, write
    from proposalbench.report.export import explorer as write_explorer

    rel = Release.load(release)
    data = build(rel, RESULTS)
    target = out or DATA_ROOT.parent / "release" / rel.release
    for p in write(data, target):
        typer.echo(str(p))
    if update_readme(DATA_ROOT.parent / "README.md", leaderboard_md(data)):
        typer.echo("README.md results table updated")
    if explorer is not None:
        typer.echo(f"{len(write_explorer(data, RESULTS, explorer))} explorer files in {explorer}")


@app.command("compare")
def compare(
    a: Annotated[str, typer.Option(help="System id.")],
    b: Annotated[str, typer.Option(help="System id to compare against.")],
    eval_id: Annotated[str, typer.Option(help="Results folder name.")] = "pilot",
    tasks_file: Annotated[
        Path | None, typer.Option(help="Restrict to the task ids in this file.")
    ] = None,
    sample: Annotated[int, typer.Option(help="Sample compared on each task.")] = 1,
) -> None:
    """Paired difference A − B on the tasks both have, with a two-way bootstrap interval."""
    from proposalbench.evaluate import RESULTS
    from proposalbench.report.export import paired

    keep = set(tasks_file.read_text().split()) if tasks_file else None
    scores: dict[str, dict[str, float]] = {a: {}, b: {}}
    for system in (a, b):
        for p in sorted((RESULTS / eval_id / system).glob(f"*/*/{sample}/score.json")):
            s = json.loads(p.read_text())
            if keep is None or s["task"] in keep:
                scores[system][s["task"]] = s["scorecard"]["score"]
    r = paired(scores[a], scores[b], Repository())
    if not r["n"]:
        raise typer.Exit(1)
    typer.echo(
        f"{a} {r['mean_a']} vs {b} {r['mean_b']} on {r['n']} tasks: "
        f"{r['diff']:+.2f} [{r['ci_low']:+.2f}, {r['ci_high']:+.2f}], "
        f"wins {r['wins']}, ties {r['ties']}, losses {r['losses']}"
    )


@app.command("power")
def power(
    eval_id: Annotated[str, typer.Option(help="Results folder name.")] = "pilot",
    k: Annotated[int, typer.Option(help="Samples per task in the planned design.")] = 2,
    comparisons: Annotated[int, typer.Option(help="Pre-registered primary comparisons.")] = 2,
) -> None:
    """Estimate variance components from evaluated samples and print MDE by number of tasks."""
    from collections import defaultdict

    from proposalbench.evaluate import RESULTS
    from proposalbench.report.leaderboard import load_scores
    from proposalbench.scoring.stats import mde, sample_sd, task_difference_sd

    scores: dict[tuple[str, str], list[float]] = defaultdict(list)
    for s in load_scores(RESULTS / eval_id):
        scores[(s["system"], s["task"])].append(s["scorecard"]["score"])
    sd_s, sd_t = sample_sd(scores), task_difference_sd(scores, k=2)
    typer.echo(f"sample SD = {sd_s}, task-difference SD = {sd_t} (from {len(scores)} cells)")
    if sd_s is None or sd_t is None:
        raise typer.Exit(1)
    for n in (10, 14, 20, 30, 40):
        m = mde(sd_t, sd_s, k, n, comparisons=comparisons)
        typer.echo(f"n_tasks={n:3}  MDE={m:5.1f} points (k={k}, {comparisons} comparisons)")


if __name__ == "__main__":
    app()
