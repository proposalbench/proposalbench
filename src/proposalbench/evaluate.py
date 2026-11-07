"""Evaluate one submission end to end, writing every stage to disk.

results/<eval_id>/<system>/<split>/<task>/<sample>/
    evaluated.md        the text as judged (truncated beyond the limit where the call says so)
    admissibility.json  checks.json  style.json  references.json
    judges/<model>.json claims/<model>.json  score.json
    claims_adjudication/candidates.json, <model>.json   pooled candidate claims and rulings

A stage whose output file exists is not recomputed, so an interrupted evaluation resumes and a
published results folder can be re-scored without calling any model or API.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import asdict
from pathlib import Path
from typing import Any

import yaml

from proposalbench.checks.admissibility import check_admissibility
from proposalbench.checks.fact_sheet import (
    FactSheet,
    check_fact_sheet,
    extract_fact_sheet,
    merge_fact_sheets,
)
from proposalbench.checks.hygiene import (
    check_dates_beyond,
    check_hygiene,
    check_required_sections,
    check_undefined_references,
)
from proposalbench.checks.style import style_profile
from proposalbench.evidence.cache import EvidenceCache
from proposalbench.evidence.http import EvidenceClient
from proposalbench.evidence.match import MatchConfig
from proposalbench.evidence.verify import ReferenceVerdict, RefStatus, verify_references
from proposalbench.judge.claims import (
    AdjudicationRun,
    Claim,
    ClaimsRun,
    adjudicate,
    adjudicated_consensus,
    candidates,
    run_claims,
)
from proposalbench.judge.items import items_for, section_metric
from proposalbench.judge.panel import aggregate, judge_error_rates
from proposalbench.judge.runner import ItemJudgment, JudgeRun, item_digest, run_judge
from proposalbench.judge.support import (
    Pair,
    SupportRun,
    build_pairs,
    cited_reference_indices,
    run_support,
)
from proposalbench.judge.support import consensus as support_consensus
from proposalbench.llm import ModelSpec
from proposalbench.parse.references import ParsedReference, parse_references
from proposalbench.parse.sections import parse_proposal
from proposalbench.scoring.score import score
from proposalbench.systems.base import Submission
from proposalbench.tasks.loader import ResolvedTask

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "results"
JUDGE_CONFIGS = ROOT / "configs" / "judges"


def load_panel(name_or_path: str) -> tuple[str, list[ModelSpec]]:
    path = Path(name_or_path)
    if not path.is_file():
        path = JUDGE_CONFIGS / f"{name_or_path}.yaml"
    cfg = yaml.safe_load(path.read_text(encoding="utf-8"))
    specs = [
        ModelSpec(
            j["provider"], j["id"], j.get("max_output_tokens", 12000), j.get("temperature", 0.0)
        )
        for j in cfg["judges"]
    ]
    return cfg["id"], specs


def _dump(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False, default=str), encoding="utf-8")


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _verdict_from_dict(d: dict) -> ReferenceVerdict:
    from proposalbench.evidence.records import WorkRecord

    ref = ParsedReference(**d["ref"])
    best = WorkRecord(**d["best"]) if d.get("best") else None
    return ReferenceVerdict(
        ref,
        RefStatus(d["status"]),
        d["indexable"],
        best,
        d["title_score"],
        d["author_match"],
        d["year_delta"],
        d["checked_sources"],
        d["notes"],
    )


def _judge_run_from_dict(d: dict) -> JudgeRun:
    return JudgeRun(
        d["judge"],
        [ItemJudgment(**j) for j in d["judgments"]],
        d["calls"],
        d.get("input_tokens", 0),
        d.get("output_tokens", 0),
        d.get("item_digests", {}),
    )


def _fact_sheet_from_dict(d: dict) -> FactSheet:
    from proposalbench.checks.fact_sheet import Dated, WorkPackage

    d = dict(d)
    d["work_packages"] = [WorkPackage(**w) for w in d.get("work_packages", [])]
    d["deliverables"] = [Dated(**x) for x in d.get("deliverables", [])]
    d["milestones"] = [Dated(**x) for x in d.get("milestones", [])]
    return FactSheet(**d)


def _claims_from_dict(d: dict) -> ClaimsRun:
    return ClaimsRun(d["judge"], [Claim(**c) for c in d["claims"]], d["raw"], d.get("error", ""))


def _check_only(item) -> bool:
    """Items whose criteria are all deterministic checks are never sent to a judge."""
    return bool(item.criteria) and not item.judged_criteria


def deterministic_metrics(
    verdicts: list[ReferenceVerdict],
    counted_words: int,
    body: str,
    irrelevant: set[int] | frozenset[int] = frozenset(),
) -> dict[str, float]:
    """Numbers that criteria with a ``check`` or ``requires`` can refer to.

    Evidence-base counts use references cited in the text, at most three per sentence, leaving
    out ``irrelevant`` references (the panel found them unrelated to, or contradicting, the
    sentence citing them); the ``listed_*`` counts describe the reference list (diagnostics).
    """
    verified = {RefStatus.VERIFIED, RefStatus.VERIFIED_WITH_ERRORS}
    dossier = {RefStatus.DOSSIER, RefStatus.DOSSIER_MISCITED}
    is_external = [v.status not in dossier | {RefStatus.UNPARSEABLE} for v in verdicts]
    cited = cited_reference_indices(body, verdicts) - set(irrelevant)
    external = sum(1 for i in cited if is_external[i])
    return {
        "verified_external_references": sum(1 for i in cited if verdicts[i].status in verified),
        "external_references": external,
        "external_references_per_1k_words": round(1000 * external / max(1, counted_words), 3),
        "listed_external_references": sum(is_external),
        "listed_verified_references": sum(1 for v in verdicts if v.status in verified),
        "dossier_references": sum(1 for v in verdicts if v.status in dossier),
        "references": len(verdicts),
    }


def section_metrics(call, checks: list[dict]) -> dict[str, float]:
    """``section_present_<id>`` per core required section (0 when reported missing)."""
    missing = {
        f.get("data", {}).get("section_id")
        for f in checks
        if f.get("check") == "structure.missing_section"
    }
    return {
        section_metric(s.id): 0.0 if s.id in missing else 1.0
        for s in call.required_sections
        if s.core
    }


PLAN_CHECKS = (
    "duration_over_max",
    "activity_after_end",
    "wp_month_order",
    "undefined_wp",
    "budget_over_cap",
    "budget_below_minimum",
    "budget_inconsistent",
    "person_months_mismatch",
    "consortium_below_minimum",
)


def plan_metrics(sheet: FactSheet, call, findings) -> dict[str, float]:
    """``plan_<check>_ok`` = 1 passed, 0 fired; absent when the sheet cannot support the check."""
    e = call.eligibility
    dated = [d.month for d in sheet.deliverables + sheet.milestones if d.month is not None]
    dated += [wp.end_month for wp in sheet.work_packages if wp.end_month is not None]
    applicable = {
        "duration_over_max": sheet.duration_months is not None
        and e.duration_months_max is not None,
        "activity_after_end": (
            sheet.duration_months is not None or e.duration_months_max is not None
        )
        and bool(dated),
        "wp_month_order": any(
            wp.start_month is not None and wp.end_month is not None for wp in sheet.work_packages
        ),
        "undefined_wp": bool(sheet.work_packages),
        "budget_over_cap": e.budget_in_narrative
        and sheet.requested_budget is not None
        and e.max_budget is not None,
        "budget_below_minimum": e.budget_in_narrative
        and sheet.requested_budget is not None
        and e.min_budget is not None,
        "budget_inconsistent": len(sheet.budget_mentions) >= 2,
        "person_months_mismatch": sheet.total_person_months is not None
        and bool(sheet.work_packages)
        and all(wp.person_months is not None for wp in sheet.work_packages),
        "consortium_below_minimum": e.consortium is not None and bool(sheet.partners),
    }
    fired = {f.check.removeprefix("plan.") for f in findings if f.kind == "deduction"}
    return {
        f"plan_{name}_ok": 0.0 if name in fired else 1.0
        for name in PLAN_CHECKS
        if applicable[name] or name in fired
    }


class SourceUnavailable(RuntimeError):
    """An evidence source the run is configured to use is temporarily out (e.g. its quota)."""


def _proposal_digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _retire_if_regenerated(out: Path, proposal: str) -> None:
    """Move stored results of an earlier text of this submission out of the scored tree.

    Every stage below reuses what is stored in OUT, so results of a regenerated proposal must
    not meet the old ones. They go to ``<eval>/_stale/<old digest>/...`` (kept, never scored).
    Results stored before digests were recorded carry none and are trusted.
    """
    stamp = out / "submission.sha256"
    if not stamp.is_file():
        return
    old = stamp.read_text().strip()
    if old == _proposal_digest(proposal):
        return
    root = out.parents[3]
    dest = root / "_stale" / old[:16] / out.relative_to(root)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(out), str(dest))


def evaluate_submission(
    rt: ResolvedTask,
    sub: Submission,
    out: Path,
    panel: list[ModelSpec],
    evidence_cache: Path,
    offline: bool = False,
) -> dict:
    _retire_if_regenerated(out, sub.proposal)
    out.mkdir(parents=True, exist_ok=True)
    (out / "submission.sha256").write_text(_proposal_digest(sub.proposal) + "\n")
    adm_path = out / "admissibility.json"
    if not adm_path.is_file():
        adm = check_admissibility(sub.proposal, rt.call)
        (out / "evaluated.md").write_text(adm.evaluated_text, encoding="utf-8")
        d = asdict(adm)
        d.pop("evaluated_text")
        _dump(adm_path, d)
    adm_d = _load(adm_path)
    evaluated = (out / "evaluated.md").read_text(encoding="utf-8")
    parsed = parse_proposal(evaluated)

    if not (out / "checks.json").is_file():
        findings = check_hygiene(parsed) + check_required_sections(
            parsed, rt.call.required_sections
        )
        _dump(out / "checks.json", [f.to_dict() for f in findings])
        _dump(out / "style.json", style_profile(parsed, rt.call.language).to_dict())

    ref_path = out / "references.json"
    if not ref_path.is_file():
        refs = parse_references(parsed.references_block or "")
        with (
            EvidenceCache(evidence_cache) as cache,
            EvidenceClient(cache, offline=offline) as client,
        ):
            verdicts = verify_references(refs, rt.dossier.own_publications, client, MatchConfig())
            if spent := {
                host: why
                for host, why in client.unavailable_sources.items()
                if not why.startswith("disabled")
            }:
                # A source that ran out mid-run (a daily quota) would give this proposal a
                # smaller source set than the others; nothing is stored and it is evaluated
                # again once the source is back.
                raise SourceUnavailable(f"evaluation deferred: {spent}")
            _dump(
                ref_path,
                {
                    "verdicts": [asdict(v) for v in verdicts],
                    "events": client.events,
                    "unavailable_sources": client.unavailable_sources,
                },
            )
    verdicts = [_verdict_from_dict(v) for v in _load(ref_path)["verdicts"]]

    items = items_for(rt)
    runs: list[JudgeRun] = []
    claim_runs: list[ClaimsRun] = []
    if adm_d["admissible"]:
        for spec in panel:
            jp = out / "judges" / f"{spec.model_id.replace('/', '_')}.json"
            if not jp.is_file():
                if offline:
                    raise RuntimeError(f"offline replay is missing {jp}")
                _dump(jp, run_judge(spec, rt, parsed, items).to_dict())
            run = _judge_run_from_dict(_load(jp))
            # Items added to the rubric after this run, and items the judge returned nothing
            # for (a failed or truncated batch), are judged on their own and merged, so neither
            # a rubric extension nor a transient failure requires re-judging the whole proposal.
            # Only absent answers are retried, never a verdict the judge actually gave.
            # An item whose wording changed since it was judged (same id, new digest) is
            # re-judged too. Runs from before digests were recorded carry none and are trusted.
            seen = {j.item_id for j in run.judgments if j.verdict != "missing"}
            seen -= {
                i.id for i in items if run.item_digests.get(i.id, item_digest(i)) != item_digest(i)
            }
            missing = [i for i in items if i.id not in seen and not _check_only(i)]
            if missing and not offline:
                extra = run_judge(spec, rt, parsed, missing)
                retried = {j.item_id for j in extra.judgments}
                run.judgments = [j for j in run.judgments if j.item_id not in retried]
                run.judgments += extra.judgments
                run.calls += extra.calls
                run.input_tokens += extra.input_tokens
                run.output_tokens += extra.output_tokens
                run.item_digests.update(extra.item_digests)
                _dump(jp, run.to_dict())
            runs.append(run)
            cp = out / "claims" / f"{spec.model_id.replace('/', '_')}.json"
            if not cp.is_file():
                if offline:
                    raise RuntimeError(f"offline replay is missing {cp}")
                _dump(cp, run_claims(spec, rt, evaluated).to_dict())
            claim_runs.append(_claims_from_dict(_load(cp)))

    pairs_path = out / "support" / "pairs.json"
    if not pairs_path.is_file():
        if offline:
            raise RuntimeError(f"offline replay is missing {pairs_path}")
        with EvidenceCache(evidence_cache) as cache, EvidenceClient(cache) as client:
            pairs, info = build_pairs(parsed.body_text(), verdicts, client)
        _dump(pairs_path, {"info": info, "pairs": [asdict(p) for p in pairs]})
    pairs_d = _load(pairs_path)
    pairs = [Pair(**p) for p in pairs_d["pairs"]]
    support_runs: list[SupportRun] = []
    if adm_d["admissible"] and pairs:
        for spec in panel:
            sp = out / "support" / f"{spec.model_id.replace('/', '_')}.json"
            if not sp.is_file():
                if offline:
                    raise RuntimeError(f"offline replay is missing {sp}")
                _dump(sp, run_support(spec, pairs).to_dict())
            support_runs.append(SupportRun(**_load(sp)))
    support = (
        support_consensus(pairs, support_runs) if support_runs else {"defects": [], "counts": {}}
    )

    sheet_findings: list = []
    plan: dict[str, float] = {}
    if adm_d["admissible"]:
        sheets: list[FactSheet] = []
        for spec in panel:
            fp = out / "factsheet" / f"{spec.model_id.replace('/', '_')}.json"
            if not fp.is_file():
                if offline:
                    raise RuntimeError(f"offline replay is missing {fp}")
                sheet, record = extract_fact_sheet(spec, evaluated, rt.call)
                _dump(fp, {"sheet": asdict(sheet) if sheet else None, "record": record})
            d = _load(fp)["sheet"]
            sheets.append(_fact_sheet_from_dict(d) if d else FactSheet())
        merged = merge_fact_sheets(sheets)
        # Undefined work packages and aims are also checked in the text: the extracted sheet
        # misses them when judges relabel identifiers.
        sheet_findings = (
            check_fact_sheet(merged, rt.call)
            + check_undefined_references(parsed)
            + check_dates_beyond(parsed, rt.call.eligibility.duration_months_max)
        )
        plan = plan_metrics(merged, rt.call, sheet_findings)
        _dump(
            out / "factsheet" / "merged.json",
            {"sheet": asdict(merged), "findings": [f.to_dict() for f in sheet_findings]},
        )

    agreed_claims: list[Claim] = []
    if claim_runs:
        cands = candidates(claim_runs)
        adj_dir = out / "claims_adjudication"
        _dump(adj_dir / "candidates.json", [asdict(c) for c in cands])
        adj_runs = []
        for spec in panel:
            ap = adj_dir / f"{spec.model_id.replace('/', '_')}.json"
            stale = ap.is_file() and _load(ap).get("quotes") != [c.quote for c in cands]
            if not ap.is_file() or stale:
                if offline:
                    raise RuntimeError(f"offline replay is missing {ap}")
                _dump(ap, adjudicate(spec, rt, evaluated, cands).to_dict())
            adj_runs.append(AdjudicationRun(**_load(ap)))
        agreed_claims = adjudicated_consensus(cands, adj_runs)

    irrelevant = {d["ref_index"] for d in support["defects"]}
    metrics = (
        deterministic_metrics(verdicts, adm_d["counted_words"], parsed.body_text(), irrelevant)
        | section_metrics(rt.call, _load(out / "checks.json"))
        | plan
    )
    item_results = aggregate(items, runs, metrics=metrics) if runs else []
    card = score(adm_d["admissible"], item_results, verdicts, agreed_claims, support["defects"])
    summary = {
        "task": rt.id,
        "system": sub.meta.system_id,
        "sample": sub.meta.sample,
        "submission_status": sub.meta.status,
        "scorecard": card.to_dict(),
        "items": [asdict(i) for i in item_results],
        "claims": [asdict(c) for c in agreed_claims],
        "judge_error_rates": judge_error_rates(runs),
        "references": {s.value: sum(1 for v in verdicts if v.status == s) for s in RefStatus},
        "counted_words": adm_d["counted_words"],
        "metrics": metrics,
        "support": {"info": pairs_d["info"], "counts": support["counts"]},
        "plan_findings": [f.to_dict() for f in sheet_findings],
    }
    if sub.meta.status != "ok":
        summary["scorecard"]["score"] = 0.0
    _dump(out / "score.json", summary)
    return summary
