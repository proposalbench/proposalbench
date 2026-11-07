"""Build the maintainer review page for the v2 public tasks.

Collects the 20 new calls (with the official sources their skeleton was verified against and
the automated review history, including reviewer points the author rejected), every v2 trap,
and a stratified sample of full task bundles, and writes one self-contained HTML page from
``review_packet.html``. The page stores the maintainer's verdicts in its artifact database
(collection ``verdicts``), so they can be read back and acted on.

    uv run python tools/authoring/review_packet.py            # -> .work/review/v2-review.html
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import date
from pathlib import Path

import yaml

from proposalbench.tasks.loader import Repository

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
MATRIX_V2 = HERE / "public_matrix_v2.yaml"
REVIEWS = HERE / "reviews"
DRAFTS = HERE / "drafts"
TEMPLATE = HERE / "review_packet.html"
OUT = ROOT / ".work" / "review" / "v2-review.html"

# One task per scheme; together: every task type, five close and five stretch, each dossier
# author family three or four times, and every harder-dossier variant (thin, inconsistent,
# cross-language both ways, both kinds of resubmission).
SAMPLE = [
    "pub2-ka220-studios-stretch",
    "pub2-cerv-service-close",
    "pub2-he-stage1-coast-stretch",
    "pub2-he-coldchain-stretch",
    "pub2-nih-transition-close",
    "pub2-he-revision-coast-stretch",
    "pub2-nsf-inference-close",
    "pub2-erc-workflow-close",
    "pub2-aei-care-stretch",
    "pub2-foundation-signals-close",
]

TRAP_TYPES = {
    "T01": ("Budget beyond the call's limits", 7),
    "T02": ("Duration or phases beyond the call", 7),
    "T03": ("Applicant eligibility", 7),
    "T04": ("Consortium rules", 6),
    "T05": ("Excluded activity", 7),
    "T06": ("Pending presented as secured", 7),
    "T07": ("Planned presented as existing", 6),
    "T08": ("Overstated track record or collaboration", 7),
    "T09": ("Missing mandatory element or template section", 7),
    "T10": ("Data integrity", 6),
    "T11": ("Scope drift", 6),
    "T12": ("Silent dossier fact", 8),
    "T13": ("Reviewer criticism not addressed", 6),
    "T14": ("Ethics, data protection, regulatory status", 6),
}

FAMILY = {"anthropic": "Claude Opus", "google": "Gemini", "openai": "GPT-6"}


def _json(path: Path) -> dict | None:
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None


def _review_summary(kind: str, uid: str) -> list[dict]:
    """The automated reviews of a unit, first opinion first."""
    out = []
    for suffix in (".prev.json", ".json"):
        r = _json(REVIEWS / f"{kind}-{uid}{suffix}")
        if not r:
            continue
        sev = Counter(i.get("severity") for i in r.get("issues", []))
        out.append(
            {
                "reviewer": FAMILY.get(r.get("reviewer_family"), r.get("reviewer_family")),
                "verdict": r.get("verdict"),
                "blocker": sev.get("blocker", 0),
                "major": sev.get("major", 0),
                "minor": sev.get("minor", 0),
            }
        )
    return out


def _rejected(kind: str, uid: str) -> list[dict]:
    """Reviewer points the author declined to fix, with the author's reason."""
    d = _json(DRAFTS / f"{kind}-{uid}.json")
    out = []
    for h in (d or {}).get("history", []):
        issues = h.get("review_issues", [])
        for r in h.get("rejected") or []:
            if isinstance(r, str):  # some authors give only their reason
                out.append({"problem": "", "reason": r})
                continue
            problem = r.get("problem") or r.get("issue") or ""
            if not problem and r.get("index") is not None and r["index"] < len(issues):
                problem = issues[r["index"]].get("problem", "")
            if not problem and r.get("checklist"):
                match = [i for i in issues if i.get("checklist") == r["checklist"]]
                problem = match[0].get("problem", "") if match else ""
            out.append({"problem": problem, "reason": r.get("reason", "")})
    return out


def _variant(rt) -> list[str]:
    d = rt.dossier
    v = []
    if d.gaps:
        v.append("thin dossier")
    if d.inconsistencies:
        v.append("inconsistent dossier")
    if d.reviewer_criticisms:
        v.append("resubmission dossier")
    if d.language != rt.call.language:
        v.append(f"cross-language ({d.language} dossier, {rt.call.language} call)")
    return v


def build() -> dict:
    m = yaml.safe_load(MATRIX_V2.read_text(encoding="utf-8"))
    tasks = {rt.id: rt for rt in Repository().all()}
    v2 = [tasks[t["id"]] for t in m["tasks"]]
    call_specs = {c["id"]: c for c in m["calls"]}

    calls = []
    for spec in m["calls"]:
        rt = next(t for t in v2 if t.call.id == spec["id"])
        call = rt.call
        skel_name = spec.get("skeleton", spec["scheme"])
        skel = yaml.safe_load((HERE / "schemes" / f"{skel_name}.yaml").read_text("utf-8"))
        e = call.eligibility
        calls.append(
            {
                "id": call.id,
                "title": call.title,
                "topic_code": call.topic_code,
                "scheme": call.scheme.value,
                "template": skel_name,
                "language": call.language,
                "proposal_type": call.proposal_type.value,
                "author": FAMILY.get(spec["author"], spec["author"]),
                "max_words": call.length_contract.max_words,
                "enforcement": call.length_contract.enforcement.value,
                "currency": e.currency,
                "max_budget": e.max_budget,
                "min_budget": e.min_budget,
                "duration_max": e.duration_months_max,
                "sections": [s.title for s in call.required_sections],
                "sources": [s["url"] for s in skel.get("sources") or []],
                "reviews": _review_summary("call", call.id),
                "rejected": _rejected("call", call.id),
                "tasks": [
                    {"id": t.id, "fit": t.task.fit_level.value} for t in v2 if t.call.id == call.id
                ],
                "text": rt.call_text,
            }
        )

    traps = []
    for rt in v2:
        for tr in rt.task.traps:
            traps.append(
                {
                    "key": f"trap__{rt.id}__{tr.id}",
                    "task": rt.id,
                    "trap": tr.id,
                    "type": tr.type,
                    "fit": rt.task.fit_level.value,
                    "task_type": rt.task.type,
                    "call": rt.call.id,
                    "call_title": rt.call.title,
                    "dossier": rt.dossier.id,
                    "variant": _variant(rt),
                    "description": tr.description,
                    "expected": tr.expected_behaviour,
                    "rejected": _rejected("task", rt.id),
                }
            )
    briefs = {rt.id: rt.brief_text or "" for rt in v2}

    counts = Counter(
        tr.type for rt in tasks.values() if rt.task.split.value == "public" for tr in rt.task.traps
    )
    v2_counts = Counter(t["type"] for t in traps)
    types = [
        {
            "type": k,
            "name": name,
            "target": target,
            "total": counts.get(k, 0),
            "v2": v2_counts.get(k, 0),
        }
        for k, (name, target) in TRAP_TYPES.items()
    ]

    sample = []
    for tid in SAMPLE:
        rt = tasks[tid]
        d = rt.dossier
        sample.append(
            {
                "id": rt.id,
                "call": rt.call.id,
                "call_title": rt.call.title,
                "scheme": call_specs[rt.call.id].get("skeleton", rt.call.scheme.value),
                "task_type": rt.task.type,
                "fit": rt.task.fit_level.value,
                "author": FAMILY.get(rt.task.provenance.author_family or "", ""),
                "variant": _variant(rt),
                "brief": rt.brief_text or "",
                "files": [{"path": p, "text": t} for p, t in rt.dossier_texts().items()],
                "traps": [
                    {
                        "id": t.id,
                        "type": t.type,
                        "description": t.description,
                        "expected": t.expected_behaviour,
                    }
                    for t in rt.task.traps
                ],
                "gaps": [g.text for g in d.gaps],
                "inconsistencies": [i.text for i in d.inconsistencies],
                "criticisms": [{"id": c.id, "text": c.text} for c in d.reviewer_criticisms],
                "facts": [
                    {
                        "id": f.id,
                        "kind": f.kind.value,
                        "text": f.text,
                        "value": f.value,
                        "source": f.source,
                    }
                    for f in d.facts
                ],
                "reviews": _review_summary("task", rt.id),
                "dossier_reviews": _review_summary("dossier", d.id),
                "rejected": _rejected("task", rt.id) + _rejected("dossier", d.id),
            }
        )

    return {
        "built": date.today().isoformat(),
        "calls": calls,
        "traps": traps,
        "trap_types": types,
        "briefs": briefs,
        "sample": sample,
    }


def main() -> None:
    data = json.dumps(build(), ensure_ascii=False).replace("</", "<\\/")
    html = TEMPLATE.read_text(encoding="utf-8").replace("/*__DATA__*/{}", data)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} ({len(html) / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
