"""Release export: every number the README, the paper and the results page show, from one run.

A release config (``configs/release/<release>.yaml``) names the published systems and the
headline tasks. Systems it doesn't list are left out of every output. Two views are exported:

- ``headline``: sample 1 of every published system on the headline tasks (the tasks the headline
  system was not developed on), compared pairwise on the same tasks;
- ``full``: every scored sample of the other published systems on all tasks of the split.
"""

from __future__ import annotations

import csv
import json
import re
import statistics
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from itertools import combinations
from pathlib import Path

import yaml

from proposalbench.report import costs
from proposalbench.report.leaderboard import Row, cluster_bootstrap, leaderboard
from proposalbench.scoring.agreement import summary as agreement_summary
from proposalbench.systems.base import SUBMISSIONS
from proposalbench.tasks.loader import DATA_ROOT, Repository

ROOT = DATA_ROOT.parent
NOT_DISCLOSED = "not_disclosed"
RELEASES = ROOT / "configs" / "release"
PANELS = ROOT / "configs" / "judges"


@dataclass
class Release:
    eval_id: str
    release: str
    title: str
    judge_panel: str
    systems: dict[str, dict]
    headline_system: str
    headline_tasks: list[str]
    featured_schemes: list[str]
    # Commercial systems whose generation cost is not published.
    undisclosed_cost: list[str] = field(default_factory=list)

    @classmethod
    def load(cls, name_or_path: str | Path) -> Release:
        path = Path(name_or_path)
        if not path.suffix:
            path = RELEASES / f"{name_or_path}.yaml"
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        return cls(**{k: data[k] for k in cls.__dataclass_fields__ if k in data})

    def published(self, s: dict) -> bool:
        return s["system"] in self.systems

    def headline(self, s: dict) -> bool:
        return self.published(s) and s["sample"] == 1 and s["task"] in self.headline_tasks

    def full(self, s: dict) -> bool:
        return self.published(s) and s["system"] != self.headline_system


def scored(results_dir: Path, keep) -> list[tuple[Path, dict]]:
    out = []
    for p in sorted(results_dir.glob("*/*/*/*/score.json")):
        s = json.loads(p.read_text(encoding="utf-8"))
        if keep(s):
            out.append((p.parent, s))
    return out


def paired(a: dict[str, float], b: dict[str, float], repo: Repository) -> dict:
    """Mean of a − b over the tasks both have, with a two-way (calls × dossiers) bootstrap
    interval and win/tie/loss counts."""
    tasks = sorted(set(a) & set(b))
    if not tasks:
        return {"n": 0}
    d = [a[t] - b[t] for t in tasks]
    calls = [repo.get(t).call.id for t in tasks]
    dossiers = [repo.get(t).dossier.id for t in tasks]
    lo, hi = cluster_bootstrap(d, calls, dossiers)
    return {
        "n": len(tasks),
        "mean_a": round(statistics.mean(a[t] for t in tasks), 2),
        "mean_b": round(statistics.mean(b[t] for t in tasks), 2),
        "diff": round(statistics.mean(d), 2),
        "ci_low": lo,
        "ci_high": hi,
        "wins": sum(x > 0 for x in d),
        "ties": sum(x == 0 for x in d),
        "losses": sum(x < 0 for x in d),
    }


def _by_system_task(samples: list[tuple[Path, dict]]) -> dict[str, dict[str, float]]:
    out: dict[str, dict[str, float]] = defaultdict(dict)
    for _, s in samples:
        out[s["system"]][s["task"]] = s["scorecard"]["score"]
    return out


def _groups(samples: list[tuple[Path, dict]], key) -> dict[str, dict[str, dict]]:
    """system -> group -> {mean, n}."""
    acc: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for _, s in samples:
        acc[s["system"]][key(s["task"])].append(s["scorecard"]["score"])
    return {
        sys_: {
            g: {"mean": round(statistics.mean(v), 2), "n": len(v)} for g, v in sorted(gs.items())
        }
        for sys_, gs in acc.items()
    }


def _consistency(samples: list[tuple[Path, dict]]) -> dict[str, dict]:
    """Sample 1 vs sample 2 on the same task, for systems run twice."""
    by: dict[str, dict[str, dict[int, float]]] = defaultdict(lambda: defaultdict(dict))
    for _, s in samples:
        by[s["system"]][s["task"]][s["sample"]] = s["scorecard"]["score"]
    out = {}
    for sys_, tasks in sorted(by.items()):
        pairs = [(v[1], v[2]) for v in tasks.values() if 1 in v and 2 in v]
        if len(pairs) < 3:
            continue
        x, y = zip(*pairs, strict=True)
        r = statistics.correlation(x, y) if len(set(x)) > 1 and len(set(y)) > 1 else None
        out[sys_] = {
            "n": len(pairs),
            "mean_abs_diff": round(statistics.mean(abs(a - b) for a, b in pairs), 2),
            "pearson_r": None if r is None else round(r, 3),
        }
    return out


def _models(meta: dict) -> list[str]:
    for note in meta.get("notes", []):
        if note.startswith("models used:"):
            return [m.strip() for m in note.split(":", 1)[1].split(",") if m.strip()]
    return [m["model_id"] for m in meta.get("models", [])]


def _meta(submissions_dir: Path, results_dir: Path, d: Path) -> dict:
    path = submissions_dir / d.relative_to(results_dir) / "meta.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def sample_rows(
    samples: list[tuple[Path, dict]],
    release: Release,
    repo: Repository,
    results_dir: Path,
    submissions_dir: Path,
    prices: dict[str, costs.Price],
) -> list[dict]:
    rows = []
    for d, s in samples:
        rt = repo.get(s["task"])
        meta = _meta(submissions_dir, results_dir, d)
        kind, tool = costs.system_tool(s["system"])
        gen = costs.generation_cost(meta, prices, tool) if meta else costs.Cost(None, None)
        if s["system"] in release.undisclosed_cost:
            gen = costs.Cost(None, NOT_DISCLOSED)
        c, refs = s["scorecard"], s["references"]
        severities = defaultdict(int)
        for defect in c.get("defects", []):
            severities[defect.get("severity", "other")] += 1
        g = granular(s, _style(d))
        rows.append(
            {
                "system": s["system"],
                "task": s["task"],
                "sample": s["sample"],
                "headline": release.headline(s),
                "scheme": rt.call.scheme.value,
                "fit": rt.task.fit_level.value,
                "score": c["score"],
                "quality": c["quality"],
                "call_responsiveness": c["components"].get("call_responsiveness"),
                "substance": c["components"].get("substance"),
                "grounding": c["components"].get("grounding"),
                "deductions": c["deductions"],
                "critical_defects": severities["critical"],
                "major_defects": severities["major"],
                "minor_defects": severities["minor"],
                "admissible": c["admissible"],
                "counted_words": s["counted_words"],
                "max_words": rt.call.length_contract.max_words,
                "refs_total": sum(refs.values()),
                "refs_verified": refs.get("verified", 0) + refs.get("verified_with_errors", 0),
                "refs_not_found": refs.get("not_found", 0),
                "wall_time_s": meta.get("wall_time_s"),
                "gen_cost_usd": gen.usd,
                "gen_cost_basis": gen.basis,
                "subscription": kind == "cli",
                "judge_cost_usd": costs.judging_cost(d, prices),
                **g,
            }
        )
    return rows


EXTERNAL_REF_KINDS = (
    "verified",
    "verified_with_errors",
    "misattributed",
    "doi_unresolved",
    "not_found",
    "unparseable",
)
SUPPORT_JUDGED = ("supports", "partial", "unrelated", "contradicts")


def _style(d: Path) -> dict:
    p = d / "style.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def granular(score: dict, style: dict) -> dict:
    """Per-proposal counts behind the granular metrics (pooled per system by ``metrics``)."""
    refs = score["references"]
    counts = (score.get("support") or {}).get("counts") or {}
    kinds = defaultdict(int)
    for defect in score["scorecard"].get("defects", []):
        kinds[defect["kind"]] += 1
    traps = [
        i["score"]
        for i in score["items"]
        if i["item_id"].startswith("TRAP-") and i["status"] == "scored" and i["score"] is not None
    ]
    return {
        "ext_refs": sum(refs.get(k, 0) for k in EXTERNAL_REF_KINDS),
        "refs_unverifiable": refs.get("not_found", 0)
        + refs.get("misattributed", 0)
        + refs.get("doi_unresolved", 0),
        "refs_fabricated": refs.get("misattributed", 0) + refs.get("doi_unresolved", 0),
        "cites_checked": sum(counts.get(k, 0) for k in SUPPORT_JUDGED),
        "cites_supported": counts.get("supports", 0),
        "cites_unsupported": counts.get("unrelated", 0) + counts.get("contradicts", 0),
        "applicant_claims": sum(v for k, v in kinds.items() if k.startswith("applicant_")),
        "dossier_miscited": kinds["metadata_dossier_miscited"],
        "traps_score": round(statistics.mean(traps), 4) if traps else None,
        "em_dashes_per_1k": style.get("em_dashes_per_1k"),
        "buzzwords_per_1k": style.get("buzzwords_per_1k"),
    }


def _ratio(num: float, den: float) -> float | None:
    return round(num / den, 4) if den else None


def _mean(xs: list) -> float | None:
    vals = [x for x in xs if x is not None]
    return round(statistics.mean(vals), 4) if vals else None


def metrics(rows: list[dict]) -> dict[str, dict]:
    """Granular metrics per system from sample rows: shares are pooled over the system's
    references or checked citations; per-proposal figures are means."""
    by: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by[r["system"]].append(r)
    out = {}
    for sys_id, rs in sorted(by.items()):
        out[sys_id] = {
            "proposals": len(rs),
            "refs_per_proposal": _mean([r["ext_refs"] for r in rs]),
            "unverifiable_refs": _ratio(
                sum(r["refs_unverifiable"] for r in rs), sum(r["ext_refs"] for r in rs)
            ),
            "fabricated_refs": _ratio(
                sum(r["refs_fabricated"] for r in rs), sum(r["ext_refs"] for r in rs)
            ),
            "supported_citations": _ratio(
                sum(r["cites_supported"] for r in rs), sum(r["cites_checked"] for r in rs)
            ),
            "unsupported_citations": _ratio(
                sum(r["cites_unsupported"] for r in rs), sum(r["cites_checked"] for r in rs)
            ),
            "applicant_claims_per_proposal": _mean([r["applicant_claims"] for r in rs]),
            "dossier_miscited_per_proposal": _mean([r["dossier_miscited"] for r in rs]),
            "traps_caught": _mean([r["traps_score"] for r in rs]),
            "rejected": round(1 - statistics.mean(1.0 if r["admissible"] else 0.0 for r in rs), 4),
            "em_dashes_per_1k": _mean([r["em_dashes_per_1k"] for r in rs]),
            "buzzwords_per_1k": _mean([r["buzzwords_per_1k"] for r in rs]),
        }
    return out


def _systems(
    release: Release, samples: list[tuple[Path, dict]], results_dir: Path, submissions_dir: Path
) -> dict[str, dict]:
    out = {}
    for sys_id, info in release.systems.items():
        mine = [(d, s) for d, s in samples if s["system"] == sys_id]
        metas = [_meta(submissions_dir, results_dir, d) for d, _ in mine]
        models = sorted({m for meta in metas for m in _models(meta)})
        dates = sorted(meta["created_at"][:10] for meta in metas if meta.get("created_at"))
        kind, _ = costs.system_tool(sys_id)
        out[sys_id] = {
            **info,
            "models": info.get("models") or models,
            "versions": sorted({meta.get("system_version") for meta in metas} - {None}),
            "generated": [dates[0], dates[-1]] if dates else None,
            "subscription": kind == "cli",
            "samples": len(mine),
        }
    return out


def _judges(release: Release, samples: list[tuple[Path, dict]], results_dir: Path, prices):
    panel = yaml.safe_load((PANELS / f"{release.judge_panel}.yaml").read_text(encoding="utf-8"))
    measured = [c for d, _ in samples if (c := costs.judging_cost(d, prices)) is not None]
    run = costs.run_judging_cost(results_dir)
    return {
        "panel": [j["id"] for j in panel["judges"]],
        "measured": {
            "evaluations": len(measured),
            "mean_usd": round(statistics.mean(measured), 2) if measured else None,
            "median_usd": round(statistics.median(measured), 2) if measured else None,
        },
        "run_average": run,
        "agreement": agreement_summary(d for d, _ in samples),
    }


def _rows(rows: list[Row], release: Release) -> list[dict]:
    out = []
    for r in rows:
        d = {**asdict(r), "name": release.systems[r.system]["name"]}
        if r.system in release.undisclosed_cost:
            d |= {"gen_cost": None, "gen_cost_basis": NOT_DISCLOSED}
        out.append(d)
    return out


def build(
    release: Release, results_root: Path, submissions_dir: Path = SUBMISSIONS
) -> dict[str, object]:
    """Everything a release shows, as plain data."""
    results_dir = results_root / release.eval_id
    repo = Repository()
    prices = costs.load_prices()
    published = scored(results_dir, release.published)
    headline = [(d, s) for d, s in published if release.headline(s)]
    full = [(d, s) for d, s in published if release.full(s)]

    head_scores = _by_system_task(headline)
    head_rows = leaderboard(results_dir, submissions_dir, release.headline)
    order = [r.system for r in head_rows]
    full_rows = leaderboard(results_dir, submissions_dir, release.full)
    hs = release.headline_system
    versus = {
        other: paired(head_scores[hs], head_scores[other], repo) for other in order if other != hs
    }
    matrix = {
        f"{a}|{b}": paired(head_scores[a], head_scores[b], repo) for a, b in combinations(order, 2)
    }

    def scheme(t: str) -> str:
        return repo.get(t).call.scheme.value

    def fit(t: str) -> str:
        return repo.get(t).task.fit_level.value

    rows = sample_rows(published, release, repo, results_dir, submissions_dir, prices)
    all_public = sorted({s["task"] for _, s in full})
    development = sorted(set(all_public) - set(release.headline_tasks))
    featured = []
    for sch in release.featured_schemes:
        tasks = sorted(t for t in release.headline_tasks if scheme(t) == sch)
        if tasks:
            rt = repo.get(tasks[0])
            featured.append(
                {
                    "task": rt.id,
                    "scheme": sch,
                    "fit": rt.task.fit_level.value,
                    "call_title": rt.call.title,
                    "max_words": rt.call.length_contract.max_words,
                }
            )
    return {
        "meta": {
            "release": release.release,
            "title": release.title,
            "eval_id": release.eval_id,
            "headline_system": hs,
            "headline_tasks": release.headline_tasks,
            "development_tasks": development,
            "tasks_in_split": len(all_public),
            "exported_at": datetime.now(UTC).isoformat(timespec="seconds"),
        },
        "systems": _systems(release, published, results_dir, submissions_dir),
        "headline": {
            "leaderboard": _rows(head_rows, release),
            "versus_headline": versus,
            "pairs": matrix,
            "by_scheme": _groups(headline, scheme),
            "by_fit": _groups(headline, fit),
            "metrics": metrics([r for r in rows if r["headline"]]),
        },
        "full": {
            "leaderboard": _rows(full_rows, release),
            "by_scheme": _groups(full, scheme),
            "consistency": _consistency(full),
        },
        "judges": _judges(release, published, results_dir, prices),
        "featured": featured,
        "samples": rows,
    }


_DIGITS = ["Zero", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine"]


def macro_name(*parts: str) -> str:
    """A LaTeX-safe macro name: letters only, CamelCase, digits spelled out."""
    words = re.split(r"[^A-Za-z0-9]+", " ".join(parts))
    out = ""
    for w in words:
        w = re.sub(r"\d", lambda m: _DIGITS[int(m.group())], w)
        out += w[:1].upper() + w[1:]
    return "pb" + out


def numbers_tex(data: dict) -> str:
    lines = [f"% Generated by `pb export` for release {data['meta']['release']}; do not edit."]

    def add(name: str, value) -> None:
        lines.append(f"\\newcommand{{\\{name}}}{{{value}}}")

    meta = data["meta"]
    add(macro_name("headline", "tasks"), len(meta["headline_tasks"]))
    add(macro_name("development", "tasks"), len(meta["development_tasks"]))
    add(macro_name("split", "tasks"), meta["tasks_in_split"])
    add(macro_name("systems"), len(data["systems"]))
    for view in ("headline", "full"):
        for rank, row in enumerate(data[view]["leaderboard"], 1):
            sys_ = row["system"]
            add(macro_name(view, sys_, "score"), f"{row['score']:.1f}")
            add(macro_name(view, sys_, "ci"), f"[{row['ci_low']:.1f}, {row['ci_high']:.1f}]")
            add(macro_name(view, sys_, "rank"), rank)
            add(macro_name(view, sys_, "n"), row["samples"])
            if row["gen_minutes"] is not None:
                add(macro_name(view, sys_, "minutes"), f"{row['gen_minutes']:.1f}")
            if row["gen_cost"] is not None:
                add(macro_name(view, sys_, "cost"), f"{row['gen_cost']:.2f}")
    for other, p in data["headline"]["versus_headline"].items():
        add(macro_name("versus", other, "diff"), f"{p['diff']:+.1f}")
        add(macro_name("versus", other, "ci"), f"[{p['ci_low']:+.1f}, {p['ci_high']:+.1f}]")
        add(macro_name("versus", other, "wins"), f"{p['wins']}/{p['n']}")
    j = data["judges"]["measured"]
    if j["mean_usd"] is not None:
        add(macro_name("judge", "cost", "mean"), f"{j['mean_usd']:.2f}")
    return "\n".join(lines) + "\n"


KIND_LABEL = {"product": "product", "agent": "agent", "direct": "single prompt"}
README_START, README_END = "<!-- results:start -->", "<!-- results:end -->"


def _usd(value: float | None, basis: str | None, subscription: bool) -> str:
    if basis == NOT_DISCLOSED:
        return "not disclosed"
    if value is None:
        return "—"
    text = f"${value:.2f}"
    if basis == "upper_bound":
        text = "≤" + text
    elif basis == "estimated":
        text += " est."
    return text + (" †" if subscription else "")


def leaderboard_md(data: dict) -> str:
    """The headline table for the README, with its footnote."""
    meta = data["meta"]
    lines = [
        "| # | System | Type | Score [95% CI] | Cost per proposal | Minutes per proposal |",
        "|---|---|---|---|---|---|",
    ]
    for rank, r in enumerate(data["headline"]["leaderboard"], 1):
        info = data["systems"][r["system"]]
        minutes = "—" if r["gen_minutes"] is None else f"{r['gen_minutes']:.1f}"
        lines.append(
            f"| {rank} | {r['name']} | {KIND_LABEL.get(info['kind'], info['kind'])} | "
            f"{r['score']:.1f} [{r['ci_low']:.1f}, {r['ci_high']:.1f}] | "
            f"{_usd(r['gen_cost'], r['gen_cost_basis'], r['subscription'])} | {minutes} |"
        )
    lines += [
        "",
        f"Sample 1 of every system on the {len(meta['headline_tasks'])} public tasks that "
        "Proposia Pro was not developed on. Scores run from 0 to 100; intervals are a two-way "
        "bootstrap over calls and dossiers. Cost and time are medians per proposal and are not "
        "scored: *est.* is recorded tokens × list prices, *≤* an upper bound (cache hits priced "
        "as uncached input), and † the API-equivalent cost of a run made on a subscription. "
        "Proposia Pro is a commercial product; its generation cost is not disclosed.",
    ]
    return "\n".join(lines)


def update_readme(readme: Path, table: str) -> bool:
    """Replace the text between the results markers; False when the README has no markers."""
    text = readme.read_text(encoding="utf-8")
    if README_START not in text or README_END not in text:
        return False
    head, rest = text.split(README_START, 1)
    _, tail = rest.split(README_END, 1)
    readme.write_text(f"{head}{README_START}\n{table}\n{README_END}{tail}", encoding="utf-8")
    return True


def write(data: dict, out: Path) -> list[Path]:
    out.mkdir(parents=True, exist_ok=True)
    written = []

    def dump(name: str, obj) -> None:
        p = out / name
        p.write_text(json.dumps(obj, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        written.append(p)

    dump("release.json", {k: v for k, v in data.items() if k != "samples"})
    samples = data["samples"]
    p = out / "samples.csv"
    with p.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(samples[0]))
        w.writeheader()
        w.writerows(samples)
    written.append(p)
    p = out / "numbers.tex"
    p.write_text(numbers_tex(data), encoding="utf-8")
    written.append(p)
    p = out / "leaderboard.md"
    p.write_text(leaderboard_md(data) + "\n", encoding="utf-8")
    written.append(p)
    return written


def explorer(
    data: dict, results_root: Path, out: Path, submissions_dir: Path = SUBMISSIONS
) -> list[Path]:
    """One JSON per (featured task, system): the proposal and its scorecard, for the page."""
    eval_dir = results_root / data["meta"]["eval_id"]
    written = []
    for f in data["featured"]:
        for sys_id in data["systems"]:
            rel = Path(sys_id) / "public" / f["task"] / "1"
            score_path, proposal = (
                eval_dir / rel / "score.json",
                submissions_dir / rel / "proposal.md",
            )
            if not score_path.exists() or not proposal.exists():
                continue
            s = json.loads(score_path.read_text(encoding="utf-8"))
            c = s["scorecard"]
            doc = {
                "system": sys_id,
                "task": f["task"],
                "score": c["score"],
                "quality": c["quality"],
                "components": c["components"],
                "deductions": c["deductions"],
                "defects": [
                    {k: d.get(k) for k in ("kind", "severity", "points", "detail")}
                    for d in c.get("defects", [])
                ],
                "references": s["references"],
                "counted_words": s["counted_words"],
                "proposal": proposal.read_text(encoding="utf-8"),
            }
            p = out / f["task"] / f"{sys_id}.json"
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(json.dumps(doc, ensure_ascii=False) + "\n", encoding="utf-8")
            written.append(p)
    return written
