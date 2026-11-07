from proposalbench.checks.fact_sheet import Dated, FactSheet, WorkPackage, check_fact_sheet
from proposalbench.evaluate import plan_metrics
from proposalbench.judge.items import generic_items
from proposalbench.judge.panel import aggregate
from proposalbench.tasks.loader import Repository


def test_plan_metrics_only_report_checkable_checks_and_feed_pc1():
    call = Repository().get("pilot-he-soilwater-close").call  # 48 months, EUR 6M cap
    sheet = FactSheet(
        duration_months=48,
        requested_budget=6_500_000,
        budget_currency="EUR",
        work_packages=[WorkPackage("WP1", "Field", 1, 48, "IABE", None)],
        milestones=[Dated("MS1", "End", 50, "WP1")],
    )
    findings = check_fact_sheet(sheet, call)
    m = plan_metrics(sheet, call, findings)
    assert m["plan_duration_over_max_ok"] == 1.0
    assert m["plan_activity_after_end_ok"] == 0.0
    assert m["plan_budget_over_cap_ok"] == 0.0
    assert "plan_person_months_mismatch_ok" not in m  # no effort figures: not checkable
    assert "plan_consortium_below_minimum_ok" not in m  # no partners extracted

    pc1 = next(i for i in generic_items() if i.id == "PC1")
    (res,) = aggregate([pc1], [], metrics=m)
    met = sum(1 for v in res.criteria.values() if v == "met")
    counted = sum(1 for v in res.criteria.values() if v in ("met", "not_met"))
    assert res.score == met / counted and res.score < 1


def test_empty_sheet_leaves_pc1_unscored():
    call = Repository().get("pilot-he-soilwater-close").call
    sheet = FactSheet()
    m = plan_metrics(sheet, call, check_fact_sheet(sheet, call))
    pc1 = next(i for i in generic_items() if i.id == "PC1")
    (res,) = aggregate([pc1], [], metrics=m)
    assert res.score is None
