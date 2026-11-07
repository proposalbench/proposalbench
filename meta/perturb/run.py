"""Write paired interventions, optionally evaluate them, and summarise detector performance."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import statistics
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, replace
from pathlib import Path

from meta.perturb.operators import OPERATORS, ROOT, TAXONOMY, Detector, Expectation
from proposalbench.judge.quote_verify import normalize
from proposalbench.systems.base import SUBMISSIONS, Submission, SubmissionMeta
from proposalbench.tasks.loader import Repository


def _read(path, default=None):
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else default


def _write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def wilson(successes: int, total: int) -> tuple[float, float] | None:
    """Two-sided Wilson score interval, z=1.959963984540054 (95%)."""
    if total < 0 or not 0 <= successes <= total:
        raise ValueError("Require 0 <= successes <= total.")
    if total == 0:
        return None
    z = 1.959963984540054
    p = successes / total
    denominator = 1 + z * z / total
    centre = (p + z * z / (2 * total)) / denominator
    half = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denominator
    return max(0.0, centre - half), min(1.0, centre + half)


def load_result(folder: Path) -> dict:
    data = {
        name: _read(folder / f"{name}.json")
        for name in ("checks", "admissibility", "references", "score")
    }
    plan = _read(folder / "factsheet/merged.json")
    plan_findings = (data["score"] or {}).get("plan_findings", [])
    if plan is not None:
        plan_findings = plan.get("findings", plan_findings)
    data["text_plan_available"] = bool(
        (plan is not None and "findings" in plan)
        or "plan_findings" in (data["score"] or {})
        or any(f.get("check", "").startswith("plan.") for f in (data["checks"] or []))
        or (data["admissibility"] or {}).get("admissible") is False
    )
    if plan_findings:
        data["checks"] = (data["checks"] or []) + plan_findings
    claim_runs = [_read(p) for p in sorted((folder / "claims").glob("*.json"))]
    data["claims_available"] = bool(
        data["score"] is not None
        and "claims" in data["score"]
        and (data["admissibility"] or {}).get("admissible", True)
        and (not claim_runs or sum(not r.get("error") for r in claim_runs) > len(claim_runs) / 2)
    )
    # Arithmetic is deterministic, but plan extraction uses judges. Do not claim its absence
    # is a true negative when an older evaluator never ran the fact-sheet stage.
    data["plan_available"] = bool(
        plan is not None
        or list(folder.glob("fact_sheet*.json"))
        or list(folder.glob("fact_sheet/**/*.json"))
        or any(f.get("check", "").startswith("plan.") for f in (data["checks"] or []))
    )
    return data


def _matches(text, target):
    if not target:
        return True
    text, target = normalize(text), normalize(target)
    return target in text or (len(text.split()) >= 4 and text in target)


def _item(data, item_id):
    return next(
        (i for i in (data.get("score") or {}).get("items", []) if i.get("item_id") == item_id), None
    )


def _number(data, detector):
    score = data.get("score") or {}
    if detector.kind == "score_increase":
        # A failed/abstained evaluator producing zero quality is not an invariance success.
        card = score.get("scorecard", {})
        return (
            card.get("score")
            if card.get("quality") is not None and data.get("claims_available") is not False
            else None
        )
    if detector.kind == "component_drop":
        return score.get("scorecard", {}).get("components", {}).get(detector.values[0])
    item = _item(data, detector.values[0])
    if not item or item.get("status", "scored") != "scored":
        return None
    return item.get("score")


def fires(
    detector: Detector,
    data: dict,
    baseline: dict | None = None,
    *,
    control=False,
    score_tolerance=3.0,
):
    """True/False for an observed event, None for missing data or abstention.

    Score drops/increases are relative to baseline; static findings are scoped by the manifest.
    ``item_change`` compares every judged criterion, excluding explicitly deterministic ones.
    """
    kind = detector.kind
    if kind == "invariance":
        return invariance_facets(data, baseline or {}, score_tolerance)[detector.values[0]][
            "changed"
        ]
    target = detector.control_target if control else detector.target
    if kind == "check":
        name = (
            "admissibility"
            if all(v.startswith("admissibility.") for v in detector.values)
            else "checks"
        )
        findings = data.get(name)
        if findings is None:
            return None
        if any(v.startswith("plan.") for v in detector.values) and not data.get("plan_available"):
            return None
        if isinstance(findings, dict):
            findings = findings.get("findings", [])
        return any(
            f.get("check") in detector.values
            and (
                not detector.section_id
                or f.get("data", {}).get("section_id") == detector.section_id
            )
            for f in findings
        )
    if kind == "reference":
        if data.get("references") is None:
            return None
        refs = data["references"].get("verdicts", [])
        selected = [
            r
            for r in refs
            if detector.ref_index is None or r.get("ref", {}).get("index") == detector.ref_index
        ]
        if not selected:
            return False  # a completed verifier that dropped the target missed the flaw
        return any(
            r.get("status") in detector.values
            and (not detector.note or detector.note in r.get("notes", []))
            for r in selected
        )
    if kind in {"defect", "claim"}:
        if data.get("score") is None:
            return None
        if kind == "defect":
            entries = data["score"].get("scorecard", {}).get("defects", [])
            return any(
                d.get("kind") in detector.values
                and _matches(d.get("detail", ""), target)
                and (not detector.severity or d.get("severity") == detector.severity)
                for d in entries
            )
        if data.get("claims_available") is False:
            return None
        return any(
            c.get("type") in detector.values
            and _matches(c.get("quote", ""), target)
            and (not detector.severity or c.get("severity") == detector.severity)
            for c in data["score"].get("claims", [])
        )
    if kind == "item_change":
        if baseline is None:
            return None
        a, b = _item(data, detector.values[0]), _item(baseline, detector.values[0])
        if not a or not b:
            return None
        a, b = a.get("criteria", {}), b.get("criteria", {})
        keys = (a.keys() | b.keys()) - set(detector.exclude_criteria)
        valid = {"met", "not_met", "split", "na"}
        if not keys or any(a.get(k) not in valid or b.get(k) not in valid for k in keys):
            return None
        return any(a[k] != b[k] for k in keys)
    if kind not in {"item_drop", "component_drop", "score_increase"}:
        raise ValueError(f"Unknown detector kind: {kind}")
    if baseline is None:
        return None
    a, b = _number(data, detector), _number(baseline, detector)
    if a is None or b is None:
        return None
    return a > b + 1e-8 if kind == "score_increase" else a < b - 1e-8


def _deltas(a, b):
    a, b = (a.get("score") or {}), (b.get("score") or {})
    ca, cb = a.get("scorecard", {}), b.get("scorecard", {})

    def delta(x, y):
        return round(x - y, 6) if x is not None and y is not None else None

    return {
        "score": delta(ca.get("score"), cb.get("score")),
        "quality": delta(ca.get("quality"), cb.get("quality")),
        "components": {
            k: delta(v, cb.get("components", {}).get(k))
            for k, v in ca.get("components", {}).items()
        },
        "items": {
            i["item_id"]: delta(
                i.get("score"),
                next(
                    (j.get("score") for j in b.get("items", []) if j["item_id"] == i["item_id"]),
                    None,
                ),
            )
            for i in a.get("items", [])
        },
    }


def _finding_key(finding):
    data = finding.get("data") or {}
    # These identify the subject without quotes, offsets, paragraph boundaries or formatting.
    # Numeric measurements (word counts/confidence) do not define a new finding.
    key = {k: data[k] for k in ("family", "id", "month", "bound", "order", "style") if k in data}
    return (
        finding.get("check", ""),
        str(data["section_id"])
        if "section_id" in data
        else json.dumps(key, sort_keys=True, ensure_ascii=False),
    )


def _deterministic_snapshot(data):
    if any(data.get(k) is None for k in ("checks", "admissibility", "references")):
        return None
    if not data.get("text_plan_available"):
        return None
    findings = list(data["checks"]) + data["admissibility"].get("findings", [])
    keys = {
        _finding_key(f)
        for f in findings
        if not f.get("check", "").startswith("plan.")
        or f["check"] == "plan.undefined_wp"
        or (
            f["check"] == "plan.activity_after_end"
            and f.get("data", {}).get("bound") == "call_maximum_text"
        )
    }
    counts = Counter(r["status"] for r in data["references"].get("verdicts", []))
    return keys, counts


def invariance_facets(transformed, control, score_tolerance=3.0):
    """Pair measurements; missing judges never make deterministic findings unavailable."""
    score_detector = Detector("score", "score_increase")
    a, b = _number(transformed, score_detector), _number(control, score_detector)
    delta = round(a - b, 6) if a is not None and b is not None else None
    score = {
        "difference": delta,
        "absolute_difference": abs(delta) if delta is not None else None,
        "tolerance": score_tolerance,
        "changed": abs(delta) > score_tolerance if delta is not None else None,
    }
    p, c = _deterministic_snapshot(transformed), _deterministic_snapshot(control)
    findings = {"changed": None, "added": [], "removed": [], "reference_status_counts": None}
    if p is not None and c is not None:
        findings = {
            "changed": p != c,
            "added": sorted(p[0] - c[0]),
            "removed": sorted(c[0] - p[0]),
            "reference_status_counts": {"transformed": dict(p[1]), "control": dict(c[1])},
        }
    ids = {
        i["item_id"]
        for d in (transformed, control)
        for i in (d.get("score") or {}).get("items", [])
    }
    differences = {}
    for item_id in sorted(ids):
        detector = Detector(item_id, "item_drop", (item_id,))
        a, b = _number(transformed, detector), _number(control, detector)
        differences[item_id] = round(a - b, 6) if a is not None and b is not None else None
    moved = {k: v for k, v in differences.items() if v is not None and abs(v) > 0.25}
    complete = bool(ids) and all(v is not None for v in differences.values())
    items = {
        "differences": differences,
        "moved": moved,
        "tolerance": 0.25,
        "changed": True if moved else False if complete else None,
    }
    return {"score": score, "findings": findings, "items": items}


def _compare(expectation, perturbed, control, base):
    results = []
    for detector in expectation.detectors:
        p = fires(detector, perturbed, control, score_tolerance=expectation.score_tolerance)
        c = fires(
            detector, control, base, control=True, score_tolerance=expectation.score_tolerance
        )
        # For invariance the event is an attack success; detected means the expected resistance.
        detected = None if p is None or c is None else ((p == detector.expected) and not c)
        if detector.kind == "invariance":
            # Control-vs-old-base noise is diagnostic; it must not veto the fresh pair test.
            detected = None if p is None else p == detector.expected
        results.append(
            {
                "id": detector.id,
                "family": detector.family,
                "expected": detector.expected,
                "perturbed_fires": p,
                "control_fires": c,
                "detected": detected,
                "attack_success": p if not detector.expected else None,
            }
        )
    return {
        **(
            {
                "invariance": invariance_facets(perturbed, control, expectation.score_tolerance),
                "control_invariance": invariance_facets(
                    control, base or {}, expectation.score_tolerance
                ),
            }
            if any(d.kind == "invariance" for d in expectation.detectors)
            else {}
        ),
        "detectors": results,
        "deltas": _deltas(perturbed, control),
        "control_vs_base": _deltas(control, base or {}),
    }


def _model_views(folder, rt):
    """Reaggregate saved, validated judgments for one model; never call a model.

    Model scores use that model's items and applicant claims, and the shared reference/support
    deductions. They are diagnostics, not replacement official panel scores.
    """
    from proposalbench.evaluate import _judge_run_from_dict, _verdict_from_dict
    from proposalbench.judge.claims import Claim
    from proposalbench.judge.items import items_for
    from proposalbench.judge.panel import aggregate
    from proposalbench.scoring.score import score

    shared = load_result(folder)
    result = {}
    claims = {_read(p)["judge"]: _read(p) for p in sorted((folder / "claims").glob("*.json"))}
    adj = folder / "claims_adjudication"
    candidates = _read(adj / "candidates.json") if (adj / "candidates.json").is_file() else None
    adjudications = {
        _read(p)["judge"]: _read(p)
        for p in sorted(adj.glob("*.json"))
        if p.name != "candidates.json"
    }
    verdicts = [_verdict_from_dict(v) for v in (shared.get("references") or {}).get("verdicts", [])]
    for path in sorted((folder / "judges").glob("*.json")):
        run = _judge_run_from_dict(_read(path))
        metrics = (shared.get("score") or {}).get("metrics", {})
        items = aggregate(items_for(rt), [run], metrics=metrics)
        claim_run = claims.get(run.judge)
        own_claims = [Claim(**c) for c in claim_run.get("claims", [])] if claim_run else []
        ruling = adjudications.get(run.judge)
        if ruling is not None and candidates is not None:
            # This judge's own rulings on the pooled candidates (the panel's adjudication stage).
            own_claims = [
                Claim(c["quote"], c["type"], v, c.get("dossier_quote", ""), [run.judge], [v])
                for i, c in enumerate(candidates)
                if (v := ruling.get("verdicts", {}).get(str(i))) in ("minor", "critical")
            ]
        card = score(
            (shared.get("admissibility") or {}).get("admissible", False),
            items,
            verdicts,
            own_claims,
        ).to_dict()
        support = [
            d
            for d in (shared.get("score") or {}).get("scorecard", {}).get("defects", [])
            if d.get("kind", "").startswith("citation_")
        ]
        card["deductions"] += sum(d["points"] for d in support)
        card["defects"] += support
        if card["admissible"] and card["quality"] is not None:
            card["score"] = max(0.0, round(card["quality"] - card["deductions"], 2))
        result[run.judge] = shared | {
            # A panel-extracted fact sheet cannot be attributed to this individual judge.
            "plan_available": False,
            "claims_available": claim_run is not None and not claim_run.get("error"),
            "score": {
                "items": [asdict(i) for i in items],
                "scorecard": card,
                "claims": [asdict(c) for c in own_claims],
            },
        }
    return result


def detect(
    expectation: Expectation, perturbed: Path, control: Path, base: Path | None = None, rt=None
) -> dict:
    """Read evaluator artefacts and apply the manifest; usable independently of the runner."""
    p, c = load_result(perturbed), load_result(control)
    b = load_result(base) if base else None
    result = _compare(expectation, p, c, b)
    result["judges"] = {}
    if rt is not None:
        pv, cv = _model_views(perturbed, rt), _model_views(control, rt)
        bv = _model_views(base, rt) if base else {}
        for model in sorted(pv.keys() | cv.keys() | bv.keys()):
            result["judges"][model] = _compare(
                expectation, pv.get(model, {}), cv.get(model, {}), bv.get(model)
            )
    return result


def _rate(successes, total):
    return {
        "numerator": successes,
        "denominator": total,
        "rate": successes / total if total else None,
        "wilson95": wilson(successes, total),
    }


def _statistics(rows):
    known = [r for r in rows if r.get("detected") is not None]
    controls = [r for r in rows if r.get("control_fires") is not None]
    attacks = [r for r in rows if r.get("attack_success") is not None]
    return {
        "applicable": len(rows),
        "evaluated": len(known),
        "unavailable": len(rows) - len(known),
        # Requested denominator is all applicable pairs; publish only when observation is complete.
        "recall": _rate(sum(r["detected"] for r in known), len(rows))
        if len(known) == len(rows)
        else {
            "rate": None,
            "wilson95": None,
            "numerator": sum(r["detected"] for r in known),
            "denominator": len(rows),
        },
        "observed_recall": _rate(sum(r["detected"] for r in known), len(known)),
        "false_positive_rate": _rate(sum(r["control_fires"] for r in controls), len(controls)),
        "attack_success_rate": _rate(sum(r["attack_success"] for r in attacks), len(attacks)),
    }


def _invariance_summary(pairs, detections):
    rows = [detections.get(p["path"], {}).get("invariance", {}) for p in pairs if p["applicable"]]
    scores = [
        r["score"]["difference"] for r in rows if r.get("score", {}).get("difference") is not None
    ]

    def share(facet):
        known = [r[facet]["changed"] for r in rows if r.get(facet, {}).get("changed") is not None]
        return _rate(sum(known), len(known)) | {"unavailable": len(rows) - len(known)}

    moved = Counter(k for r in rows for k in r.get("items", {}).get("moved", {}))
    observed = Counter(
        k
        for r in rows
        for k, v in r.get("items", {}).get("differences", {}).items()
        if v is not None
    )
    return {
        "n": len(rows),
        "score_n": len(scores),
        "mean_score_difference": statistics.mean(scores) if scores else None,
        "sd_score_difference": statistics.stdev(scores) if len(scores) > 1 else None,
        "over_tolerance": share("score"),
        "finding_changes": share("findings"),
        "items_moved_most": [
            {"item_id": k, "count": n, "observed": observed[k], "share": n / observed[k]}
            for k, n in sorted(moved.items(), key=lambda kv: (-kv[1], kv[0]))
        ],
    }


def summarize(out: Path) -> dict:
    """Aggregate saved detection.json files; dry runs never turn unobserved checks into misses."""
    groups = defaultdict(list)
    operators = defaultdict(list)
    index = _read(out / "manifest.json", {"pairs": []})
    models = set(index.get("judges", []))
    detections = {}
    applicability = defaultdict(list)
    for pair in index["pairs"]:
        applicability[pair["operator"]].append(pair)
        if pair["applicable"]:
            d = _read(out / pair["path"] / "detection.json", {})
            detections[pair["path"]] = d
            models.update(d.get("judges", {}))
    for pair in index["pairs"]:
        if not pair["applicable"]:
            continue
        folder = out / pair["path"]
        expectation = Expectation.from_dict(_read(folder / "expectation.json")["expectation"])
        detection = detections[pair["path"]]
        views = {"panel": detection} | {
            model: detection.get("judges", {}).get(model, {}) for model in sorted(models)
        }
        for model, view in views.items():
            by_id = {d["id"]: d for d in view.get("detectors", [])}
            for detector in expectation.detectors:
                if model != "panel" and detector.family != "judge":
                    continue
                row = by_id.get(detector.id, {})
                groups[(model, detector.family, pair["operator"], detector.id)].append(row)
            for family in {d.family for d in expectation.detectors}:
                if model != "panel" and family != "judge":
                    continue
                rows = [by_id.get(d.id, {}) for d in expectation.detectors if d.family == family]
                known = all(r.get("detected") is not None for r in rows)
                controls = all(r.get("control_fires") is not None for r in rows)
                operators[(model, family, pair["operator"])].append(
                    {
                        "detected": all(r["detected"] for r in rows) if known else None,
                        "control_fires": any(r["control_fires"] for r in rows)
                        if controls
                        else None,
                        "attack_success": next(
                            (
                                r.get("attack_success")
                                for r in rows
                                if r.get("attack_success") is not None
                            ),
                            None,
                        ),
                    }
                )
    summary = {
        "pairs": len(index["pairs"]),
        "applicable": sum(p["applicable"] for p in index["pairs"]),
        "applicability": {
            op: {
                "applicable": sum(p["applicable"] for p in pairs),
                "attempted": len(pairs),
                "skip_reasons": dict(
                    Counter(p.get("reason", "") for p in pairs if not p["applicable"])
                ),
            }
            for op, pairs in sorted(applicability.items())
        },
        "invariance": {
            op: _invariance_summary(pairs, detections)
            for op, pairs in sorted(applicability.items())
            if "invariance" in TAXONOMY.get(op, ())
        },
        "by_operator": [
            {"judge": j, "family": f, "operator": op, **_statistics(rows)}
            for (j, f, op), rows in sorted(operators.items())
        ],
        "by_detector": [
            {"judge": j, "family": f, "operator": op, "detector": d, **_statistics(rows)}
            for (j, f, op, d), rows in sorted(groups.items())
        ],
    }
    _write(out / "summary.json", summary)
    lines = [
        "# Perturbation validation",
        "",
        f"Applicable pairs: {summary['applicable']} / {summary['pairs']}.",
        "",
        "Recall is unavailable until every applicable pair is observed. "
        "Invariance recall means resistance; attack success is reported separately.",
        "",
        "Plan checks are judge-based because their fact extraction uses models. "
        "Wilson intervals treat pairs as independent; proposals share bases and tasks.",
        "",
    ]
    lines += ["| Operator | Applicable / attempted |", "|---|---|"]
    for op, counts in summary["applicability"].items():
        lines.append(f"| {op} | {counts['applicable']}/{counts['attempted']} |")
    lines.append("")

    def display(rate):
        if rate["rate"] is None:
            return "unavailable"
        lo, hi = rate["wilson95"]
        return (
            f"{rate['rate']:.3f} [{lo:.3f}, {hi:.3f}] ({rate['numerator']}/{rate['denominator']})"
        )

    for key, title in (("by_operator", "Operators"), ("by_detector", "Detectors")):
        lines += [
            f"## {title}",
            "",
            "| Judge | Family | Operator / detector | Evaluated / applicable | "
            "Recall [95%] | Control FPR [95%] | Attack success [95%] |",
            "|---|---|---|---|---|---|---|",
        ]
        for row in summary[key]:
            name = row["operator"] + (" / " + row["detector"] if "detector" in row else "")
            lines.append(
                f"| {row['judge']} | {row['family']} | {name} | "
                f"{row['evaluated']}/{row['applicable']} | {display(row['recall'])} | "
                f"{display(row['false_positive_rate'])} | {display(row['attack_success_rate'])} |"
            )
        lines.append("")
    if summary["invariance"]:
        lines += [
            "## Meaning-preserving invariance",
            "",
            "Differences are transformed minus fresh unchanged control; SD is sample SD. "
            "Shares use observed pairs; n includes all applicable pairs. "
            "Control-versus-original-base measurements are saved separately as noise diagnostics.",
            "",
            "| Operator | n | Score n | Mean Δ | SD Δ | Over tolerance | "
            "Any deterministic finding change | Items moved > 0.25 (count/observed) |",
            "|---|---|---|---|---|---|---|---|",
        ]
        for op, row in summary["invariance"].items():
            mean = row["mean_score_difference"]
            sd = row["sd_score_difference"]
            mean = f"{mean:+.3f}" if mean is not None else "unavailable"
            sd = f"{sd:.3f}" if sd is not None else "unavailable"
            items = (
                ", ".join(
                    f"{i['item_id']} ({i['count']}/{i['observed']})"
                    for i in row["items_moved_most"]
                )
                or "none observed"
            )
            lines.append(
                f"| {op} | {row['n']} | {row['score_n']} | {mean} | {sd} | "
                f"{display(row['over_tolerance'])} | "
                f"{display(row['finding_changes'])} | {items} |"
            )
        lines.append("")
    (out / "summary.md").write_text("\n".join(lines), encoding="utf-8")
    return summary


def run(
    eval_id: str,
    out: Path,
    *,
    dry_run=False,
    seed=0,
    panel="panel-pilot",
    operators: list[str] | None = None,
    samples: list[str] | None = None,
    workers: int = 1,
    results_root: Path = ROOT / "results",
    submissions_root: Path = SUBMISSIONS,
    repository=None,
) -> dict:
    from proposalbench.evaluate import evaluate_submission, load_panel

    source = results_root / eval_id
    bases = sorted(source.glob("*/*/*/*/evaluated.md"))
    if not bases:
        raise ValueError(f"No evaluated base samples under {source}")
    # Refuse stale evaluator stages rather than silently reusing them with changed documents.
    # A pre-seeded HTTP cache (raw API responses, no evaluator stages) is allowed.
    if out.exists() and any(p.name != "evidence-cache.sqlite" for p in out.iterdir()):
        raise ValueError(f"Output must be empty (fresh results required): {out}")
    out.mkdir(parents=True, exist_ok=True)
    repo = repository or Repository()
    specs = load_panel(panel)[1] if not dry_run and panel != "none" else []
    manifest = {
        "version": 1,
        "eval": eval_id,
        "seed": seed,
        "dry_run": dry_run,
        "judges": [spec.model_id for spec in specs],
        "pairs": [],
    }
    pending = []
    unknown = set(operators or []) - set(OPERATORS)
    if unknown:
        raise ValueError(f"Unknown operators: {sorted(unknown)}")
    for path in bases:
        system, split, task, sample, _ = path.relative_to(source).parts
        if samples and sample not in samples:
            continue
        rt = repo.get(task)
        if rt.task.split.value != split:
            raise ValueError(f"Split mismatch for {path}")
        base = path.read_text(encoding="utf-8")
        references = _read(path.parent / "references.json", {}).get("verdicts", [])
        meta_path = path.parent / "meta.json"
        if not meta_path.is_file():
            meta_path = submissions_root / system / split / task / sample / "meta.json"
        if not dry_run and not meta_path.is_file():
            raise ValueError(f"Base metadata missing: {meta_path}")
        for name, operator in OPERATORS.items():
            if operators and name not in operators:
                continue
            key = f"{seed}:{system}:{split}:{task}:{sample}:{name}"
            pair_seed = int.from_bytes(hashlib.sha256(key.encode()).digest()[:8], "big")
            perturbed, control, expectation = operator(
                base, rt, random.Random(pair_seed), references=references
            )
            relative = Path(name) / system / task / sample
            record = {
                "operator": name,
                "system": system,
                "split": split,
                "task": task,
                "sample": sample,
                "seed": pair_seed,
                "base": str(path.resolve()),
                "base_meta": str(meta_path.resolve()),
                "applicable": expectation.applicable,
                "reason": expectation.reason,
                "path": str(relative),
            }
            manifest["pairs"].append(record)
            if not expectation.applicable:
                continue
            folder = out / relative
            folder.mkdir(parents=True)
            for variant, text in (("perturbed", perturbed), ("control", control)):
                (folder / f"{variant}.md").write_text(text, encoding="utf-8")
            _write(
                folder / "expectation.json",
                record
                | {
                    "expectation": expectation.to_dict(),
                    "sha256": {
                        k: hashlib.sha256(v.encode()).hexdigest()
                        for k, v in {
                            "base": base,
                            "perturbed": perturbed,
                            "control": control,
                        }.items()
                    },
                },
            )
            pending.append((folder, rt, meta_path, path.parent, expectation, perturbed, control))
    _write(out / "manifest.json", manifest)
    if not dry_run:

        def evaluate_pair(item):
            folder, rt, meta_path, base_folder, expectation, perturbed, control = item
            meta = SubmissionMeta.from_json(meta_path.read_text(encoding="utf-8"))
            # Deterministic detectors read only evaluator stages that need no model.
            judged = any(d.family != "deterministic" for d in expectation.detectors)
            for variant, text in (("perturbed", perturbed), ("control", control)):
                if variant == "control" and expectation.control_is_base:
                    continue
                suffix = "perturb" if variant == "perturbed" else "control"
                copied = replace(
                    meta, system_id=f"{meta.system_id}+{suffix}:{expectation.operator}"
                )
                destination = folder / "evaluation" / variant
                destination.mkdir(parents=True)
                (destination / "meta.json").write_text(copied.to_json(), encoding="utf-8")
                evaluate_submission(
                    rt,
                    Submission(text, copied),
                    destination,
                    specs if judged else [],
                    out / "evidence-cache.sqlite",
                )
            detection = detect(
                expectation,
                folder / "evaluation/perturbed",
                base_folder if expectation.control_is_base else folder / "evaluation/control",
                base_folder,
                rt,
            )
            _write(folder / "detection.json", detection)

        with ThreadPoolExecutor(max_workers=workers) as pool:
            list(pool.map(evaluate_pair, pending))
    return summarize(out)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--eval", default="pilot", dest="eval_id")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument(
        "--panel",
        default="panel-pilot",
        help="Judge panel, or none for deterministic stages only (no model calls).",
    )
    parser.add_argument("--operators", nargs="+", help="Run only these operators.")
    parser.add_argument("--samples", nargs="+", help="Use only these sample numbers as bases.")
    parser.add_argument("--workers", type=int, default=1, help="Pairs evaluated in parallel.")
    args = parser.parse_args()
    summary = run(**vars(args))
    print(f"Applicable (operator, sample) pairs: {summary['applicable']} / {summary['pairs']}")


if __name__ == "__main__":
    main()
