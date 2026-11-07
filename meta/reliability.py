"""Agreement between the judges of the panel, per item family.

    uv run python -m meta.reliability pilot [public-v0 ...]

Reads the saved judge runs of the given evaluations (results/<eval>/.../judges/*.json); no
model is called. Units are (evaluation, item, criterion) for atomic criteria, rated yes/no
(Krippendorff's alpha, nominal), and (evaluation, item) for yes/partial/no items (alpha,
interval: 1, 0.5, 0). Abstentions, "not applicable" and invalid answers are missing values.
Intervals are percentile bootstraps over units. Writes results/meta/reliability/summary.md.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from proposalbench.scoring.agreement import alpha, bootstrap, collect_folders

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "meta" / "reliability"


def collect(eval_ids: list[str]) -> dict[str, dict[str, list[list[float]]]]:
    """family -> kind ("binary"/"ternary") -> units."""
    return collect_folders(
        folder
        for eval_id in eval_ids
        for folder in sorted((ROOT / "results" / eval_id).glob("*/*/*/*"))
    )


def summarise(eval_ids: list[str]) -> str:
    data = collect(eval_ids)
    lines = [
        "# Judge agreement",
        "",
        f"Evaluations: {', '.join(eval_ids)}. Krippendorff's alpha across the panel's judges; "
        "binary criteria nominal, yes/partial/no items interval. Units with fewer than two valid "
        "answers are left out. Exact agreement is the share of units where all valid answers "
        "match.",
        "",
        "| Item family | Kind | Units | Alpha [95% CI] | Exact agreement |",
        "|---|---|---|---|---|",
    ]
    for fam in sorted(data):
        for kind, units in sorted(data[fam].items()):
            usable = [u for u in units if len(u) >= 2]
            a = alpha(usable, kind == "ternary")
            ci = bootstrap(usable, kind == "ternary")
            exact = sum(len(set(u)) == 1 for u in usable) / max(1, len(usable))
            shown = "n/a" if a is None else f"{a:.2f}" + (f" {list(ci)}" if ci else "")
            lines.append(f"| {fam} | {kind} | {len(usable)} | {shown} | {exact:.0%} |")
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("eval_ids", nargs="+")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    md = summarise(args.eval_ids)
    (OUT / "summary.md").write_text(md, encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()
