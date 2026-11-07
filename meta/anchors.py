"""Calibration on the anchor set: real, published proposals with real reference lists.

    uv run python -m meta.anchors [--offline]

For every anchor: verify the reference list, compute the evidence-base metrics used by EV1, and
the style profile. The reference statuses measure how often the checker fails to find a real
reference (the false-positive rate a NOT_FOUND penalty would have), split by reference class.
Writes results/meta/anchors/{per_anchor.json, summary.md}.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import numpy as np
import yaml

from proposalbench.checks.style import style_profile
from proposalbench.evaluate import deterministic_metrics
from proposalbench.evidence.cache import EvidenceCache
from proposalbench.evidence.http import EvidenceClient
from proposalbench.evidence.match import MatchConfig
from proposalbench.evidence.verify import RefStatus, verify_references
from proposalbench.parse.references import parse_references
from proposalbench.parse.sections import count_words, parse_proposal

ROOT = Path(__file__).resolve().parents[1]
ANCHORS = ROOT / "data" / "anchors"
OUT = ROOT / "results" / "meta" / "anchors"


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return round(float(max(0.0, centre - half)), 4), round(float(min(1.0, centre + half)), 4)


def analyse(offline: bool) -> tuple[list[dict], dict[str, str]]:
    rows = []
    with (
        EvidenceCache(OUT / "evidence-cache.sqlite") as cache,
        EvidenceClient(cache, offline=offline) as client,
    ):
        for d in sorted(p for p in ANCHORS.iterdir() if (p / "anchor.yaml").is_file()):
            meta = yaml.safe_load((d / "anchor.yaml").read_text(encoding="utf-8"))
            parsed = parse_proposal((d / "proposal.md").read_text(encoding="utf-8"))
            refs = parse_references(parsed.references_block or "")
            verdicts = verify_references(refs, [], client, MatchConfig())
            print(f"{meta['id']}: {len(verdicts)} references", flush=True)
            body = parsed.body_text()
            words = count_words(body)
            # The same counting as the EV1 item: references cited in the text, at most three
            # per sentence.
            metrics = deterministic_metrics(verdicts, words, body)
            verified = metrics["verified_external_references"]
            rows.append(
                {
                    "id": meta["id"],
                    "language": meta.get("language"),
                    "words": words,
                    "references": len(verdicts),
                    "verified_external": verified,
                    "external_per_1k_words": metrics["external_references_per_1k_words"],
                    "listed_per_1k_words": round(1000 * len(verdicts) / max(1, words), 3),
                    "statuses": Counter(v.status.value for v in verdicts),
                    "by_class": {
                        cls: Counter(v.status.value for v in verdicts if v.indexable == flag)
                        for cls, flag in (("indexable", True), ("other", False))
                    },
                    "not_found_examples": [
                        {
                            "raw": v.ref.raw[:200],
                            "kind": v.ref.kind_guess,
                            "indexable": v.indexable,
                            "notes": v.notes[-3:],
                        }
                        for v in verdicts
                        if v.status == RefStatus.NOT_FOUND
                    ][:15],
                    "defect_statuses": [
                        {"status": v.status.value, "raw": v.ref.raw[:200], "notes": v.notes[-3:]}
                        for v in verdicts
                        if v.status
                        in (
                            RefStatus.MISATTRIBUTED,
                            RefStatus.DOI_UNRESOLVED,
                            RefStatus.VERIFIED_WITH_ERRORS,
                        )
                    ],
                    "style": style_profile(parsed, meta.get("language") or "en").to_dict(),
                }
            )
        unavailable = client.unavailable_sources
    return rows, unavailable


def summarise(rows: list[dict], unavailable: dict[str, str]) -> str:
    tot = Counter()
    idx = Counter()
    other = Counter()
    for r in rows:
        tot.update(r["statuses"])
        idx.update(r["by_class"]["indexable"])
        other.update(r["by_class"]["other"])
    n_idx, n_oth = sum(idx.values()), sum(other.values())
    nf_idx, nf_oth = idx["not_found"], other["not_found"]
    falsely_major = sum(tot[s] for s in ("misattributed", "doi_unresolved"))
    per_1k = np.array([r["external_per_1k_words"] for r in rows])
    verified = np.array([r["verified_external"] for r in rows])
    lines = [
        "# Anchor calibration",
        "",
        f"Anchors: {len(rows)}; references: {sum(tot.values())}.",
        "",
        "Sources unavailable during the run: "
        + (", ".join(f"{h} ({r})" for h, r in sorted(unavailable.items())) or "none")
        + ".",
        "",
        "## Reference checker on real references",
        "",
        "| Class | References | Not found | Rate [95% CI] |",
        "|---|---|---|---|",
        f"| Indexable (journal article, 2000+) | {n_idx} | {nf_idx} | "
        f"{nf_idx / max(1, n_idx):.1%} {wilson(nf_idx, n_idx)} |",
        f"| Other | {n_oth} | {nf_oth} | {nf_oth / max(1, n_oth):.1%} {wilson(nf_oth, n_oth)} |",
        "",
        f"Statuses: {dict(tot)}",
        "",
        f"Major-defect statuses on real references (misattributed + doi_unresolved): "
        f"{falsely_major} of {sum(tot.values())} {wilson(falsely_major, sum(tot.values()))}. "
        "Each needs manual review: a real proposal can contain a genuinely wrong reference.",
        "",
        "Notes on those verdicts: "
        + ", ".join(
            f"{k} {v}"
            for k, v in Counter(
                n.split(":")[0]
                for r in rows
                for d in r["defect_statuses"]
                if d["status"] in ("misattributed", "doi_unresolved")
                for n in d["notes"]
                if not n.endswith(("_unavailable", "Exhausted")) and "unavailable" not in n
            ).most_common()
        )
        + ".",
        "",
        "## Evidence base (EV1 calibration)",
        "",
        f"References per 1,000 words: min {per_1k.min():.2f}, 10th pct "
        f"{np.percentile(per_1k, 10):.2f}, median {np.median(per_1k):.2f}, max {per_1k.max():.2f}.",
        f"Verified external references: min {verified.min()}, 10th pct "
        f"{np.percentile(verified, 10):.1f}, median {np.median(verified):.1f}.",
        "",
        "| Anchor | Lang | Words | Refs | Refs/1k | Verified | Not found |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append(
            f"| {r['id']} | {r['language']} | {r['words']} | {r['references']} | "
            f"{r['external_per_1k_words']} | {r['verified_external']} | "
            f"{r['statuses'].get('not_found', 0)} |"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    rows, unavailable = analyse(args.offline)
    (OUT / "per_anchor.json").write_text(
        json.dumps(rows, indent=2, ensure_ascii=False, default=lambda o: dict(o)), encoding="utf-8"
    )
    md = summarise(rows, unavailable)
    (OUT / "summary.md").write_text(md, encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()
