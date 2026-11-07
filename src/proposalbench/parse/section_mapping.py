"""Map a proposal's headings onto the call's required sections (deterministic pass).

The judge layer runs an LLM-assisted mapping for headings this pass cannot place; this module
is the fallback and the first pass, and it never guesses below its thresholds.
"""

from __future__ import annotations

from dataclasses import dataclass

from rapidfuzz import fuzz

from proposalbench.parse.sections import SECTION_NUMBER, ParsedProposal, Section, normalize_heading
from proposalbench.tasks.schema import RequiredSection

TITLE_THRESHOLD = 85


@dataclass(frozen=True)
class SectionMatch:
    required: RequiredSection
    section: Section | None
    method: str  # "number+title" | "title" | "number" | "none"
    score: float


def _strip_number(title: str) -> str:
    return SECTION_NUMBER.sub("", title)


def _title_score(required: RequiredSection, heading: str) -> float:
    h = normalize_heading(_strip_number(heading))
    candidates = [required.title, *required.aliases]
    return max(
        max(fuzz.token_set_ratio(normalize_heading(c), h), fuzz.ratio(normalize_heading(c), h))
        for c in candidates
    )


def map_sections(parsed: ParsedProposal, required: list[RequiredSection]) -> list[SectionMatch]:
    body = parsed.body_sections()
    used: set[int] = set()
    out: list[SectionMatch] = []
    for req in required:
        best: tuple[float, str, Section | None] = (0.0, "none", None)
        for s in body:
            if id(s) in used:
                continue
            score = _title_score(req, s.title)
            number_ok = s.number is not None and s.number.rstrip(".") == req.id
            if number_ok and score >= 60:
                cand = (100.0 + score, "number+title", s)
            elif score >= TITLE_THRESHOLD:
                cand = (score, "title", s)
            elif number_ok:
                cand = (50.0, "number", s)
            else:
                continue
            if cand[0] > best[0]:
                best = cand
        score, method, section = best
        if section is not None:
            used.add(id(section))
        out.append(SectionMatch(req, section, method, min(score, 100.0)))
    return out
