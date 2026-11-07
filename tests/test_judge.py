from pathlib import Path

import pytest

from proposalbench.judge.claims import Claim, ClaimsRun, consensus
from proposalbench.judge.items import (
    RUBRICS,
    generic_items,
    items_for,
    resolve_sections,
    scheme_items,
    scheme_roles,
)
from proposalbench.judge.panel import aggregate
from proposalbench.judge.quote_verify import normalize, quote_found
from proposalbench.judge.runner import ItemJudgment, JudgeRun
from proposalbench.tasks.loader import Repository

SCHEMES = [p.stem for p in (RUBRICS / "schemes").glob("*.yaml")]


def test_generic_rubric_loads_with_string_verdict_keys():
    items = generic_items()
    assert items and all(isinstance(i.yes, str) and isinstance(i.no, str) for i in items)
    assert all(set(i.evidence) <= {"yes", "partial", "no"} for i in items)
    assert len({i.id for i in items}) == len(items)


@pytest.mark.parametrize("scheme", SCHEMES)
def test_scheme_rubrics_load_and_roles_are_known(scheme):
    items = scheme_items(scheme)
    roles = scheme_roles(scheme)
    assert items and roles
    used = {r for i in generic_items() for r in i.roles}
    assert used <= set(roles), f"{scheme} lacks roles {used - set(roles)}"


def test_items_for_every_task_resolve_to_known_sections():
    for rt in Repository().all():
        ids = {s.id for s in rt.call.required_sections}
        items = items_for(rt)
        assert len({i.id for i in items}) == len(items)
        for it in items:
            assert set(resolve_sections(it, rt)) <= ids, (rt.id, it.id)
        assert any(i.id.startswith("CALL-EO") for i in items)


def test_quote_found_normalises_and_allows_ellipsis():
    text = normalize(
        "We will **measure** soil water at 40 farms — every 30 minutes — for three seasons [3, 4]."
    )
    assert quote_found("We will measure soil water at 40 farms - every 30 minutes", text)
    assert quote_found("We will measure soil water ... for three seasons", text)
    assert not quote_found("We will measure soil carbon at 40 farms", text)
    assert not quote_found("soil", text)  # too short to verify


def _run(judge, verdicts):
    return JudgeRun(judge, [ItemJudgment(i, judge, v) for i, v in verdicts.items()], [])


def test_aggregate_median_majority_and_abstention():
    items = [i for i in generic_items() if not i.criteria][:3]
    a, b, c = (i.id for i in items)
    runs = [
        _run("j1", {a: "yes", b: "invalid", c: "na"}),
        _run("j2", {a: "partial", b: "cannot_determine", c: "na"}),
        _run("j3", {a: "no", b: "yes", c: "yes"}),
    ]
    res = {r.item_id: r for r in aggregate(items, runs)}
    assert res[a].score == 0.5 and res[a].status == "scored"
    assert res[b].status == "abstained" and res[b].score is None
    assert res[c].status == "na"


def test_claims_need_majority():
    def run(judge, quotes):
        return ClaimsRun(
            judge, [Claim(q, "unsupported", "critical", "", [judge]) for q in quotes], ""
        )

    q = "The PI holds an ERC Starting Grant awarded in 2022 for soil microbiome work"
    runs = [
        run("j1", [q]),
        run("j2", [q.replace("2022", "2022 ")]),
        run("j3", ["something else entirely here"]),
    ]
    agreed = consensus(runs)
    assert len(agreed) == 1 and set(agreed[0].judges) == {"j1", "j2"}
    assert consensus([run("j1", [q]), run("j2", []), run("j3", [])]) == []


def test_rubric_files_exist():
    assert Path(RUBRICS / "generic.yaml").is_file()


def _crit_run(judge, item_id, answers):
    return JudgeRun(judge, [ItemJudgment(item_id, judge, "criteria", criteria=answers)], [])


def test_criteria_items_median_per_criterion_and_checks():
    from proposalbench.judge.panel import evaluate_check

    g02 = next(i for i in generic_items() if i.id == "G02")
    runs = [
        _crit_run("j1", "G02", {"a": "yes", "b": "yes", "c": "no"}),
        _crit_run("j2", "G02", {"a": "yes", "b": "invalid", "c": "no"}),
        _crit_run("j3", "G02", {"a": "no", "b": "no", "c": "no"}),
    ]
    (res,) = aggregate([g02], runs, metrics={"verified_external_references": 1})
    # a met (2 of 3), b split (yes vs no among two valid), c not met, d check fails
    assert res.criteria == {"a": "met", "b": "split", "c": "not_met", "d": "not_met"}
    assert res.score == (1 + 0.5 + 0 + 0) / 4
    (res2,) = aggregate([g02], runs, metrics={"verified_external_references": 5})
    assert res2.criteria["d"] == "met"
    (res3,) = aggregate([g02], runs, metrics={})
    assert res3.criteria["d"] == "unknown" and res3.score == 1.5 / 3
    assert evaluate_check("x >= 3", {"x": 3}) is True


def test_claim_severity_needs_majority_of_flagging_judges():
    def run(judge, sev):
        q = "The PI holds an ERC Starting Grant awarded in 2022 for soil microbiome work"
        return ClaimsRun(judge, [Claim(q, "unsupported", sev, "", [judge], [sev])], "")

    agreed = consensus([run("j1", "critical"), run("j2", "minor"), run("j3", "minor")])
    assert agreed[0].severity == "minor"
    agreed = consensus([run("j1", "critical"), run("j2", "critical"), run("j3", "minor")])
    assert agreed[0].severity == "critical"


def test_cluster_bootstrap_interval_contains_mean():
    from proposalbench.report.leaderboard import cluster_bootstrap

    scores = [60, 70, 65, 80, 75, 50]
    calls = ["c1", "c1", "c2", "c2", "c3", "c3"]
    dossiers = ["d1", "d2", "d2", "d3", "d3", "d1"]
    lo, hi = cluster_bootstrap(scores, calls, dossiers, n=500)
    assert lo <= sum(scores) / len(scores) <= hi
    assert lo < hi


def test_requires_gate_overrides_judges():
    g02 = next(i for i in generic_items() if i.id == "G02")
    runs = [_crit_run(j, "G02", {"a": "yes", "b": "yes", "c": "yes"}) for j in ("j1", "j2", "j3")]
    (res,) = aggregate(
        [g02], runs, metrics={"external_references": 0, "verified_external_references": 0}
    )
    assert res.criteria["a"] == "not_met_required"
    (res,) = aggregate(
        [g02], runs, metrics={"external_references": 4, "verified_external_references": 3}
    )
    assert res.criteria == {"a": "met", "b": "met", "c": "met", "d": "met"}


def test_nested_bootstrap_widens_interval_when_samples_disagree():
    from proposalbench.report.leaderboard import cluster_bootstrap

    scores = [50, 90, 48, 92, 52, 88]
    tasks = ["t1", "t1", "t2", "t2", "t3", "t3"]
    calls, dossiers = ["c1", "c1", "c2", "c2", "c3", "c3"], ["d1", "d1", "d2", "d2", "d3", "d3"]
    flat = cluster_bootstrap(scores, calls, dossiers, n=800)
    nested = cluster_bootstrap(scores, calls, dossiers, n=800, tasks=tasks)
    assert (nested[1] - nested[0]) > 3 * (flat[1] - flat[0])
