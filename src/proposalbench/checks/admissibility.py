"""Admissibility: failed output, language, and the task's length contract.

For ``disregard_excess`` contracts the text beyond the limit is cut before any judging, which
mirrors evaluators ignoring excess pages. For ``inadmissible`` contracts an over-length sample
is not scored at all.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from functools import lru_cache

from proposalbench.checks.findings import Finding
from proposalbench.parse.section_mapping import map_sections
from proposalbench.parse.sections import (
    WORD,
    ParsedProposal,
    count_words,
    parse_proposal,
    strip_markdown,
    strip_tables,
)
from proposalbench.tasks.schema import Call, Enforcement

MIN_WORDS_FOR_ATTEMPT = 300
LANGUAGE_MIN_CONFIDENCE = 0.6


@dataclass
class AdmissibilityResult:
    admissible: bool
    counted_words: int
    limit: int
    limit_with_tolerance: int
    language: str | None
    language_confidence: float
    evaluated_text: str  # the proposal as it will be judged (possibly truncated)
    truncated_words: int = 0
    findings: list[Finding] = field(default_factory=list)


@lru_cache(maxsize=1)
def _detector():
    from lingua import Language, LanguageDetectorBuilder

    langs = [
        Language.ENGLISH,
        Language.SPANISH,
        Language.GERMAN,
        Language.FRENCH,
        Language.ITALIAN,
        Language.PORTUGUESE,
        Language.GREEK,
        Language.DUTCH,
        Language.CATALAN,
    ]
    return LanguageDetectorBuilder.from_languages(*langs).build()


def detect_language(text: str) -> tuple[str | None, float]:
    sample = strip_markdown(text)[:20000]
    if count_words(sample) < 20:
        return None, 0.0
    values = _detector().compute_language_confidence_values(sample)
    if not values:
        return None, 0.0
    top = values[0]
    return top.language.iso_code_639_1.name.lower(), top.value


def counted_text(parsed: ParsedProposal, call: Call) -> str:
    """The text that counts towards the limit under the call's length contract."""
    lc = call.length_contract
    if lc.counted_sections:
        matches = {m.required.id: m for m in map_sections(parsed, call.required_sections)}
        parts = []
        for sid in lc.counted_sections:
            m = matches.get(sid)
            if m and m.section:
                parts.append(f"{m.section.title}\n{parsed.subtree_text(m.section)}")
        text = "\n\n".join(parts)
    else:
        text = parsed.body_text()
        if "title" not in lc.exempt and parsed.title:
            text = f"{parsed.title}\n{text}"
        elif "title" in lc.exempt and parsed.title and text.startswith(parsed.title):
            text = text[len(parsed.title) :]
    if "tables" in lc.exempt:
        text = strip_tables(text)
    return text


def truncate_body(markdown: str, parsed: ParsedProposal, keep_words: int) -> tuple[str, int]:
    """Cut body text after ``keep_words`` words, keeping the reference block intact."""
    refs_start = None
    if parsed.references_section is not None:
        lines = markdown.splitlines(keepends=True)
        refs_start = sum(len(line) for line in lines[: parsed.references_section.line_start])
    body = markdown[:refs_start] if refs_start is not None else markdown
    tail = markdown[refs_start:] if refs_start is not None else ""
    for seen, m in enumerate(WORD.finditer(body), start=1):
        if seen > keep_words:
            cut_at = m.start()
            dropped = len(WORD.findall(body[cut_at:]))
            marker = "\n\n[... text beyond the length limit is not evaluated ...]\n\n"
            return body[:cut_at].rstrip() + marker + tail, dropped
    return markdown, 0


_WRAPPING_FENCE = re.compile(
    r"\A\s*(`{3,}|~{3,})[ \t]*(?:markdown|md)?[ \t]*\n(.*)\n\1[ \t]*\s*\Z", re.S | re.I
)


def unwrap_fence(markdown: str) -> str:
    """A whole document wrapped in one ```markdown fence is the document itself.

    Some models wrap their entire answer in a code fence; parsed literally it has no sections
    and no counted words (seen on the public split).
    """
    m = _WRAPPING_FENCE.match(markdown)
    return m.group(2) if m and "\n" + m.group(1) not in m.group(2) else markdown


def check_admissibility(markdown: str, call: Call) -> AdmissibilityResult:
    markdown = unwrap_fence(markdown)
    parsed = parse_proposal(markdown)
    lc = call.length_contract
    limit = lc.max_words
    limit_tol = int(limit * (1 + lc.tolerance))
    words = count_words(counted_text(parsed, call))
    lang, conf = detect_language(parsed.body_text())
    result = AdmissibilityResult(
        admissible=True,
        counted_words=words,
        limit=limit,
        limit_with_tolerance=limit_tol,
        language=lang,
        language_confidence=conf,
        evaluated_text=markdown,
    )

    if count_words(parsed.body_text()) < MIN_WORDS_FOR_ATTEMPT:
        result.admissible = False
        result.findings.append(
            Finding("admissibility.failed_output", "gate", "No substantive proposal text.")
        )
        return result

    if lang != call.language and conf >= LANGUAGE_MIN_CONFIDENCE:
        result.admissible = False
        result.findings.append(
            Finding(
                "admissibility.language",
                "gate",
                f"Written in {lang!r}; the call requires {call.language!r}.",
                data={"detected": lang, "confidence": round(conf, 3)},
            )
        )

    if words > limit_tol:
        over = {"counted_words": words, "limit": limit, "tolerance": lc.tolerance}
        if lc.enforcement is Enforcement.inadmissible:
            result.admissible = False
            result.findings.append(
                Finding(
                    "admissibility.over_length",
                    "gate",
                    f"{words} counted words exceed the limit of {limit} (+{lc.tolerance:.0%}).",
                    data=over,
                )
            )
        else:
            # Cut so that the counted text stops at the limit; uncounted text before the cut
            # (e.g. exempt tables) is kept, so the cut point is shifted by the difference.
            body_words = count_words(parsed.body_text())
            keep = limit_tol + max(0, body_words - words)
            result.evaluated_text, result.truncated_words = truncate_body(markdown, parsed, keep)
            result.findings.append(
                Finding(
                    "admissibility.excess_disregarded",
                    "diagnostic",
                    f"{words} counted words exceed {limit}; "
                    f"{result.truncated_words} words beyond the limit are not evaluated.",
                    data=over | {"truncated_words": result.truncated_words},
                )
            )

    for sid, max_w in lc.per_section_max_words.items():
        for m in map_sections(parsed, call.required_sections):
            if m.required.id == sid and m.section is not None:
                n = count_words(parsed.subtree_text(m.section))
                if n > max_w * (1 + lc.tolerance):
                    gate = lc.enforcement is Enforcement.inadmissible
                    if gate:
                        result.admissible = False
                    result.findings.append(
                        Finding(
                            "admissibility.section_over_length",
                            "gate" if gate else "deduction",
                            f"Section {sid} has {n} words; limit {max_w}.",
                            location=m.section.title,
                            data={"words": n, "limit": max_w},
                        )
                    )
    return result
