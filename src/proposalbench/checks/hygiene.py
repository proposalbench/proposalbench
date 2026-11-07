"""Hygiene diagnostics: meta-commentary, duplicates, placeholders, missing sections."""

from __future__ import annotations

import re
from collections import Counter

from rapidfuzz import fuzz

from proposalbench.checks.findings import Finding
from proposalbench.parse.placeholders import find_placeholders
from proposalbench.parse.section_mapping import map_sections
from proposalbench.parse.sections import ParsedProposal, count_words, normalize_heading
from proposalbench.tasks.schema import RequiredSection

META_COMMENTARY = re.compile(
    r"\b(?:as an ai(?: language model)?|as a (?:large )?language model|i (?:hope|trust) this "
    r"(?:helps|proposal)|here(?: is|'s) (?:the|your|a) (?:complete |full |revised )?"
    r"(?:proposal|draft|document)|let me know if|feel free to|i cannot (?:verify|access)|"
    r"(?:end of (?:proposal|document))|word count\s*[:=]|"
    r"como (?:modelo de lenguaje|ia)|aquí (?:tienes|está) (?:la|tu|el) (?:propuesta|borrador)|"
    r"espero que (?:esto|esta propuesta) (?:te |le )?(?:ayude|sirva))\b",
    re.IGNORECASE,
)
DUPLICATE_MIN_WORDS = 25
DUPLICATE_SIMILARITY = 92


def _paragraphs(text: str) -> list[str]:
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]


def _repeated_sentence_runs(body: str) -> list[Finding]:
    """Repeated prose regardless of paragraph breaks: two or more consecutive sentences
    (at least DUPLICATE_MIN_WORDS words together) that occur again in the same order.
    Splitting or merging paragraphs must not hide a duplicate (invariance tests).
    """
    sentences = [
        re.sub(r"\s+", " ", sent.casefold()).strip()
        for para in _paragraphs(body)
        for sent in re.split(r"(?<=[.!?])\s+|\n", para)
    ]
    sentences = [x for x in sentences if count_words(x) >= 4]
    findings, covered = [], set()
    for i in range(len(sentences)):
        for j in range(i + 1, len(sentences)):
            if j in covered or sentences[i] != sentences[j]:
                continue
            k = 0
            while i + k < j and j + k < len(sentences) and sentences[i + k] == sentences[j + k]:
                k += 1
            words = sum(count_words(x) for x in sentences[j : j + k])
            if k >= 2 and words >= DUPLICATE_MIN_WORDS:
                covered.update(range(j, j + k))
                findings.append(
                    Finding(
                        "hygiene.duplicate_paragraph",
                        "diagnostic",
                        "A passage of several sentences is repeated verbatim.",
                        data={"text": " ".join(sentences[j : j + k])[:200]},
                    )
                )
    return findings


def check_hygiene(parsed: ParsedProposal) -> list[Finding]:
    body = parsed.body_text()
    findings: list[Finding] = []

    for m in META_COMMENTARY.finditer(body):
        findings.append(
            Finding(
                "hygiene.meta_commentary",
                "diagnostic",
                "Text addressed to the user rather than to evaluators.",
                data={"text": body[max(0, m.start() - 40) : m.end() + 40]},
            )
        )

    paras = [p for p in _paragraphs(body) if count_words(p) >= DUPLICATE_MIN_WORDS]
    norm = [re.sub(r"\s+", " ", p.casefold()) for p in paras]
    reported: set[int] = set()
    for i in range(len(norm)):
        for j in range(i + 1, len(norm)):
            if j in reported:
                continue
            short, long = sorted((norm[i], norm[j]), key=len)
            # A paragraph repeated under a lead-in label (a bold line glued to it) still counts.
            contained = (
                len(short) >= 0.6 * len(long)
                and fuzz.partial_ratio(short, long) >= DUPLICATE_SIMILARITY
            )
            if (
                norm[i] == norm[j]
                or fuzz.ratio(norm[i], norm[j]) >= DUPLICATE_SIMILARITY
                or contained
            ):
                reported.add(j)
                findings.append(
                    Finding(
                        "hygiene.duplicate_paragraph",
                        "diagnostic",
                        "A paragraph is repeated (near-)verbatim.",
                        data={"text": paras[j][:200]},
                    )
                )
    if not reported:
        findings += _repeated_sentence_runs(body)

    heads = Counter(normalize_heading(s.title) for s in parsed.body_sections())
    for title, n in heads.items():
        if n > 1:
            findings.append(
                Finding(
                    "hygiene.duplicate_heading",
                    "diagnostic",
                    f"Heading appears {n} times.",
                    data={"heading": title, "count": n},
                )
            )

    for p in find_placeholders(body):
        findings.append(
            Finding(
                "hygiene.placeholder",
                "diagnostic",
                "Unresolved placeholder.",
                data={"text": p.text, "style": p.kind},
            )
        )
    return findings


def check_required_sections(
    parsed: ParsedProposal, required: list[RequiredSection]
) -> list[Finding]:
    findings = []
    matches = map_sections(parsed, required)
    for m in matches:
        if m.method == "number":
            findings.append(
                Finding(
                    "structure.uncertain_section",
                    "diagnostic",
                    f"Section {m.required.id} matched by number only ('{m.section.title}'); "
                    "left to the LLM-assisted mapping.",
                    data={"section_id": m.required.id, "heading": m.section.title},
                )
            )
        if m.section is None:
            findings.append(
                Finding(
                    "structure.missing_section",
                    "deduction" if m.required.core else "diagnostic",
                    f"Required section {m.required.id} '{m.required.title}' not found "
                    "by the deterministic mapper.",
                    data={"section_id": m.required.id, "core": m.required.core},
                )
            )
    found = [m for m in matches if m.section is not None]
    order = [m.section.line_start for m in found]
    if order != sorted(order):
        findings.append(
            Finding(
                "structure.section_order",
                "deduction",
                "Required sections appear in a different order from the call's template.",
                data={
                    "order": [
                        m.required.id for m in sorted(found, key=lambda m: m.section.line_start)
                    ]
                },
            )
        )
    return findings


# Work packages and aims, numbered: (family, pattern with the number in the first group that
# matched). Definitions are occurrences in a heading, a table row, a bold label or at the start
# of a line or list item; every other occurrence is a reference.
ID_FAMILIES = {
    "work package": re.compile(
        r"\b(?:WP|PT)\s?(\d{1,2})\b|\bWork\s+Package\s+(\d{1,2})\b"
        r"|\bPaquete\s+de\s+trabajo\s+(\d{1,2})\b",
        re.I,
    ),
    "aim": re.compile(r"\b(?:Specific\s+)?Aim\s+(\d{1,2})\b", re.I),
}
_LINE_START = re.compile(r"^\s*(?:[-*+]\s+|\d+[.)]\s+)?(?:\*\*|__)?\s*$")


def check_undefined_references(parsed: ParsedProposal) -> list[Finding]:
    """Work packages or aims referenced in prose with a number beyond the highest one defined.

    Text-based and deliberately conservative (a gap such as WP3 between WP2 and WP4 is not
    flagged): flaw injection showed the fact-sheet route missing an "Aim 5" because two of three
    judges relabelled the aims as WP1/WP2 and listed no references.
    """
    findings = []
    lines = parsed.raw.splitlines()
    if parsed.references_section is not None:
        lines = lines[: parsed.references_section.line_start]
    for family, pattern in ID_FAMILIES.items():
        defined, referenced = set(), {}
        for line in lines:
            stripped = line.strip()
            bold = [(m.start(), m.end()) for m in re.finditer(r"\*\*[^*]+\*\*|__[^_]+__", line)]
            for m in pattern.finditer(line):
                n = int(next(g for g in m.groups() if g))
                definition = (
                    stripped.startswith(("#", "|"))
                    or any(a <= m.start() < b for a, b in bold)
                    or bool(_LINE_START.match(line[: m.start()]))
                )
                if definition:
                    defined.add(n)
                else:
                    referenced.setdefault(n, stripped[:200])
        if not defined:
            continue
        for n, context in sorted(referenced.items()):
            if n > max(defined):
                findings.append(
                    Finding(
                        "plan.undefined_wp",
                        "deduction",
                        f"{family.capitalize()} {n} is referenced but never defined.",
                        location=context,
                        data={"family": family, "id": n, "highest_defined": max(defined)},
                    )
                )
    return findings


_DATED = re.compile(
    r"\b(?:milestones?|deliverables?|hitos?|entregables?|MS\s?\d+|D\s?\d+(?:\.\d+)?)\b", re.I
)
# A milestone label at the start of a line or list item: "M1:", "- M6 (Month 30)", "**M3**".
_LABEL = re.compile(
    r"^\s*(?:[-*+]\s+|\d+[.)]\s+)?(?:\*\*|__)?M\d{1,2}(?:\.\d+)?(?:\*\*|__)?\s*[:(|—–]"
)
_MONTH = re.compile(r"\b(?:M|Months?|Mes(?:es)?)\s?(\d{1,3})\b(?!\s*(?:%|years?|años))")
_DATE_HEADER = re.compile(r"\b(?:month|mes|due|delivery|fecha|deadline|timing)\b", re.I)
_CELL_MONTH = re.compile(r"^\s*[*_]*\s*(?:M|Month\s*|Mes\s*)?(\d{1,3})\s*[*_]*\s*$", re.I)


def _cells(row: str) -> list[str]:
    return [c for c in row.strip().strip("|").split("|")]


def check_dates_beyond(parsed: ParsedProposal, max_months: int | None) -> list[Finding]:
    """Milestone or deliverable months beyond the call's maximum duration, read from the text.

    Months count inside sentences that name or label a milestone or deliverable, and in tables
    with a month or due-date column (that column's bare numbers included). Conservative: the
    bound is the call's maximum, not the proposal's own duration. Flaw injection showed the
    fact-sheet route keeping another mention of the same deliverable, or extracting no prose
    milestones at all.
    """
    if not max_months:
        return []
    lines = parsed.raw.splitlines()
    if parsed.references_section is not None:
        lines = lines[: parsed.references_section.line_start]
    found: list[tuple[int, str]] = []
    date_column: int | None = None
    in_table = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("|"):
            if re.fullmatch(r"\|?[\s:|-]+\|?", stripped):
                continue
            cells = _cells(stripped)
            if not in_table:
                in_table = True
                columns = [i for i, c in enumerate(cells) if _DATE_HEADER.search(c)]
                date_column = columns[0] if len(columns) == 1 else None
                continue  # header row
            if date_column is not None and date_column < len(cells):
                m = _CELL_MONTH.match(cells[date_column])
                if m:
                    found.append((int(m.group(1)), stripped))
            if date_column is not None or _DATED.search(stripped) or _LABEL.match(stripped):
                found += [(int(m.group(1)), stripped) for m in _MONTH.finditer(stripped)]
            continue
        in_table, date_column = False, None
        labelled = bool(_LABEL.match(stripped))
        for span in re.split(r"(?<=[.;])\s+", stripped):
            if labelled or _DATED.search(span):
                found += [(int(m.group(1)), span) for m in _MONTH.finditer(span)]
            labelled = False  # only the labelled sentence itself
    findings = []
    for month, span in found:
        if month > max_months:
            findings.append(
                Finding(
                    "plan.activity_after_end",
                    "deduction",
                    f"Month {month} is after the call's maximum duration of {max_months} months.",
                    location=span[:200],
                    data={"month": month, "bound": "call_maximum_text"},
                )
            )
    return findings
