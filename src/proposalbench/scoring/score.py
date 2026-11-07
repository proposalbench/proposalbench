"""ProposalBench Score: Quality minus integrity deductions, on admissible text.

The full rules live in docs/scoring_spec.md; this module implements them and must change only
together with that document.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

from proposalbench.evidence.verify import ReferenceVerdict, RefStatus
from proposalbench.judge.claims import Claim
from proposalbench.judge.panel import ItemResult

WEIGHTS = {"call_responsiveness": 0.4, "substance": 0.4, "grounding": 0.2}

CRITICAL = 10.0
MAJOR = 4.0
MINOR = 0.5
MINOR_CAP = 5.0

# Disabled until the false-positive rate of NOT_FOUND on real references (anchor set) is
# measured at or below 2%; see docs/scoring_spec.md.
PENALISE_INDEXABLE_NOT_FOUND = False


@dataclass
class Defect:
    kind: str
    severity: str  # critical | major | minor
    points: float
    detail: str
    taxonomy: str


@dataclass
class ScoreCard:
    admissible: bool
    components: dict[str, float | None]
    quality: float | None
    deductions: float
    score: float
    defects: list[Defect] = field(default_factory=list)
    items_scored: int = 0
    items_abstained: int = 0
    items_na: int = 0

    @property
    def has_critical(self) -> bool:
        return any(d.severity == "critical" for d in self.defects)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["has_critical"] = self.has_critical
        return d


def reference_defects(verdicts: list[ReferenceVerdict]) -> list[Defect]:
    out: list[Defect] = []
    for v in verdicts:
        label = (v.ref.raw or "")[:160]
        if v.status == RefStatus.MISATTRIBUTED:
            if "doi_points_to_different_work" in v.notes and "title_verified_elsewhere" in v.notes:
                out.append(Defect("wrong_doi_real_work", "major", MAJOR, label, "P18"))
            elif "doi_points_to_different_work" in v.notes:
                out.append(Defect("doi_to_different_work", "major", MAJOR, label, "P18"))
            else:
                out.append(Defect("misattributed_reference", "major", MAJOR, label, "P18"))
        elif v.status == RefStatus.DOI_UNRESOLVED:
            out.append(Defect("doi_unresolved", "major", MAJOR, label, "P18"))
        elif v.status == RefStatus.NOT_FOUND and v.indexable and PENALISE_INDEXABLE_NOT_FOUND:
            out.append(Defect("indexable_not_found", "major", MAJOR, label, "P18"))
        elif v.status in (RefStatus.VERIFIED_WITH_ERRORS, RefStatus.DOSSIER_MISCITED):
            out.append(Defect(f"metadata_{v.status.value}", "minor", MINOR, label, "P18"))
    return out


def claim_defects(claims: list[Claim]) -> list[Defect]:
    out = []
    for c in claims:
        if c.severity == "critical":
            out.append(Defect(f"applicant_{c.type}", "critical", CRITICAL, c.quote[:200], "P19"))
        else:
            out.append(Defect(f"applicant_{c.type}_minor", "minor", MINOR, c.quote[:200], "P19"))
    return out


def support_defects(defects: list[dict], verdicts: list[ReferenceVerdict]) -> list[Defect]:
    out = []
    for d in defects:
        ref = verdicts[d["ref_index"]].ref.raw[:120] if d["ref_index"] < len(verdicts) else ""
        out.append(
            Defect(
                f"citation_{d['verdict']}",
                "major",
                MAJOR,
                f"{ref} | cited for: {d['sentence'][:160]}",
                "P18",
            )
        )
    return out


def score(
    admissible: bool,
    items: list[ItemResult],
    reference_verdicts: list[ReferenceVerdict],
    claims: list[Claim],
    support: list[dict] | None = None,
) -> ScoreCard:
    comps: dict[str, float | None] = {}
    for comp in WEIGHTS:
        vals = [i.score for i in items if i.component == comp and i.score is not None]
        comps[comp] = round(100 * sum(vals) / len(vals), 2) if vals else None
    present = {c: w for c, w in WEIGHTS.items() if comps[c] is not None}
    quality = (
        round(sum(comps[c] * w for c, w in present.items()) / sum(present.values()), 2)
        if present
        else None
    )
    defects = (
        reference_defects(reference_verdicts)
        + claim_defects(claims)
        + support_defects(support or [], reference_verdicts)
    )
    minor = min(MINOR_CAP, sum(d.points for d in defects if d.severity == "minor"))
    deductions = round(sum(d.points for d in defects if d.severity != "minor") + minor, 2)
    final = 0.0 if not admissible or quality is None else max(0.0, round(quality - deductions, 2))
    return ScoreCard(
        admissible=admissible,
        components=comps,
        quality=quality,
        deductions=deductions,
        score=final,
        defects=defects,
        items_scored=sum(1 for i in items if i.status == "scored"),
        items_abstained=sum(1 for i in items if i.status == "abstained"),
        items_na=sum(1 for i in items if i.status == "na"),
    )
