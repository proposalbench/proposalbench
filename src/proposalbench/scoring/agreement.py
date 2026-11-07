"""Agreement between the judges of a panel, per item family (Krippendorff's alpha).

Units are (evaluation, item, criterion) for atomic criteria, rated yes/no (alpha, nominal), and
(evaluation, item) for yes/partial/no items (alpha, interval: 1, 0.5, 0). Abstentions, "not
applicable" and invalid answers are missing values. No model is called.
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from collections.abc import Iterable
from itertools import permutations
from pathlib import Path

import numpy as np

TERNARY = {"yes": 1.0, "partial": 0.5, "no": 0.0}
BINARY = {"yes": 1.0, "no": 0.0}


def family(item_id: str, criteria: bool) -> str:
    if re.match(r"CALL-(EO|SC)", item_id):
        return "call outcomes and scope (criteria)"
    if item_id.startswith("CALL-EX"):
        return "call exclusions"
    if item_id.startswith("CALL-ME"):
        return "call mandatory elements"
    if item_id.startswith("TRAP-"):
        return "traps"
    if item_id.startswith("GR"):
        return "grounding (criteria)"
    if re.match(r"G\d", item_id):
        return "generic items (criteria)" if criteria else "generic items (yes/partial/no)"
    return "scheme items"


def alpha(units: list[list[float]], interval: bool) -> float | None:
    """Krippendorff's alpha from units of pairable values (>= 2 values each)."""
    units = [u for u in units if len(u) >= 2]
    values = [v for u in units for v in u]
    n = len(values)
    if n < 2 or len(set(values)) < 2:
        return None

    def delta(a: float, b: float) -> float:
        return (a - b) ** 2 if interval else float(a != b)

    observed = (
        sum(sum(delta(a, b) for a, b in permutations(u, 2)) / (len(u) - 1) for u in units) / n
    )
    counts = defaultdict(int)
    for v in values:
        counts[v] += 1
    expected = sum(counts[a] * counts[b] * delta(a, b) for a in counts for b in counts) / (
        n * (n - 1)
    )
    return None if expected == 0 else 1 - observed / expected


def bootstrap(units: list[list[float]], interval: bool, reps: int = 1000, seed: int = 0):
    rng = np.random.default_rng(seed)
    units = [u for u in units if len(u) >= 2]
    if len(units) < 5:
        return None
    stats = []
    for _ in range(reps):
        sample = [units[i] for i in rng.integers(0, len(units), len(units))]
        a = alpha(sample, interval)
        if a is not None:
            stats.append(a)
    return (round(float(np.percentile(stats, 2.5)), 2), round(float(np.percentile(stats, 97.5)), 2))


def collect_folders(folders: Iterable[Path]) -> dict[str, dict[str, list[list[float]]]]:
    """family -> kind ("binary"/"ternary") -> units, from evaluated sample folders."""
    out: dict[str, dict[str, list[list[float]]]] = defaultdict(lambda: defaultdict(list))
    for folder in folders:
        runs = [json.loads(p.read_text()) for p in sorted((folder / "judges").glob("*.json"))]
        if len(runs) < 2:
            continue
        per_item: dict[tuple, list[float]] = defaultdict(list)
        for run in runs:
            for j in run["judgments"]:
                if j.get("criteria"):
                    for cid, v in j["criteria"].items():
                        if v in BINARY:
                            per_item[(j["item_id"], cid)].append(BINARY[v])
                elif j.get("verdict") in TERNARY:
                    per_item[(j["item_id"], None)].append(TERNARY[j["verdict"]])
        for (item_id, cid), vals in per_item.items():
            kind = "binary" if cid is not None else "ternary"
            out[family(item_id, cid is not None)][kind].append(vals)
    return out


def summary(folders: Iterable[Path]) -> list[dict]:
    """One row per (item family, kind): units, alpha with a bootstrap interval, exact agreement."""
    rows = []
    data = collect_folders(folders)
    for fam in sorted(data):
        for kind, units in sorted(data[fam].items()):
            usable = [u for u in units if len(u) >= 2]
            a = alpha(usable, kind == "ternary")
            ci = bootstrap(usable, kind == "ternary")
            rows.append(
                {
                    "family": fam,
                    "kind": kind,
                    "units": len(usable),
                    "alpha": None if a is None else round(a, 3),
                    "ci": list(ci) if ci else None,
                    "exact": round(sum(len(set(u)) == 1 for u in usable) / max(1, len(usable)), 3),
                }
            )
    return rows
