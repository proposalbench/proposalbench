"""Aggregate item verdicts across a judge panel."""

from __future__ import annotations

import operator
import re
from collections import Counter
from dataclasses import dataclass, field
from statistics import median

from proposalbench.judge.items import Item
from proposalbench.judge.runner import JudgeRun

VALUE = {"yes": 1.0, "partial": 0.5, "no": 0.0}


@dataclass
class ItemResult:
    item_id: str
    component: str
    score: float | None  # None = not scored (not applicable, or no valid verdicts)
    status: str  # "scored" | "na" | "abstained"
    verdicts: dict[str, str] = field(default_factory=dict)
    criteria: dict[str, str] = field(default_factory=dict)  # criterion id -> met/not_met/...


_CHECK = re.compile(r"^\s*(\w+)\s*(>=|<=|==|>|<)\s*(-?\d+(?:\.\d+)?)\s*$")
_OPS = {">=": operator.ge, "<=": operator.le, "==": operator.eq, ">": operator.gt, "<": operator.lt}


def evaluate_check(check: str, metrics: dict[str, float]) -> bool | None:
    """Evaluate ``"<metric> <op> <number>"``; None if the metric is unavailable."""
    m = _CHECK.match(check)
    if not m:
        raise ValueError(f"malformed check {check!r}")
    name, op, value = m.groups()
    if name not in metrics:
        return None
    return _OPS[op](metrics[name], float(value))


def _criteria_result(item: Item, runs: list[JudgeRun], need: int, metrics: dict) -> ItemResult:
    states: dict[str, str] = {}
    for crit in item.criteria:
        if crit.check:
            ok = evaluate_check(crit.check, metrics)
            states[crit.id] = "unknown" if ok is None else ("met" if ok else "not_met")
            continue
        if crit.requires and evaluate_check(crit.requires, metrics) is False:
            states[crit.id] = "not_met_required"
            continue
        answers = [
            j.criteria.get(crit.id) for run in runs for j in run.judgments if j.item_id == item.id
        ]
        valid = [1.0 if a == "yes" else 0.0 for a in answers if a in ("yes", "no")]
        na = sum(1 for a in answers if a == "na")
        if len(valid) >= need:
            v = median(valid)
            states[crit.id] = {1.0: "met", 0.0: "not_met"}.get(v, "split")
        elif na >= need:
            states[crit.id] = "na"
        else:
            states[crit.id] = "abstained"
    value = {"met": 1.0, "split": 0.5, "not_met": 0.0, "not_met_required": 0.0}
    counted = [value[v] for v in states.values() if v in value]
    verdicts = {run.judge: "criteria" for run in runs}
    if not counted:
        status = "na" if any(v == "na" for v in states.values()) else "abstained"
        return ItemResult(item.id, item.component, None, status, verdicts, states)
    score = sum(counted) / len(counted)
    return ItemResult(item.id, item.component, round(score, 4), "scored", verdicts, states)


def aggregate(
    items: list[Item],
    runs: list[JudgeRun],
    min_valid: int | None = None,
    metrics: dict[str, float] | None = None,
) -> list[ItemResult]:
    """Median of valid verdicts; an item needs ``min_valid`` judges (default: a majority).

    Criteria items: each judged criterion needs a majority of valid yes/no answers and takes
    their median (met 1, split 0.5, not met 0); checks come from ``metrics``. The item score is
    the mean over counted criteria.
    """
    need = min_valid or (len(runs) // 2 + 1)
    metrics = metrics or {}
    by_item: dict[str, dict[str, str]] = {i.id: {} for i in items}
    for run in runs:
        for j in run.judgments:
            if j.item_id in by_item:
                by_item[j.item_id][run.judge] = j.verdict
    out = []
    for item in items:
        if item.criteria:
            out.append(_criteria_result(item, runs, need, metrics))
            continue
        verdicts = by_item[item.id]
        scored = [VALUE[v] for v in verdicts.values() if v in VALUE]
        na = sum(1 for v in verdicts.values() if v == "na")
        if na >= need and na > len(scored):
            out.append(ItemResult(item.id, item.component, None, "na", verdicts))
        elif len(scored) >= need:
            out.append(
                ItemResult(item.id, item.component, float(median(scored)), "scored", verdicts)
            )
        else:
            out.append(ItemResult(item.id, item.component, None, "abstained", verdicts))
    return out


def judge_error_rates(runs: list[JudgeRun]) -> dict[str, dict[str, float]]:
    """Share of each judge's verdicts that were invalid, missing or abstentions."""
    out = {}
    for run in runs:
        c = Counter(j.verdict for j in run.judgments)
        n = max(1, sum(c.values()))
        out[run.judge] = {
            "invalid": round(c["invalid"] / n, 3),
            "missing": round(c["missing"] / n, 3),
            "cannot_determine": round(c["cannot_determine"] / n, 3),
        }
    return out
