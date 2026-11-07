"""Find in-text citations (numeric and author-year) and the sentences that carry them."""

from __future__ import annotations

import re
from dataclasses import dataclass

# [12], [3, 5], [3-5], [3–5], [1; 4-6]; not [[placeholders]] nor [text](links).
NUMERIC = re.compile(
    r"(?<!\[)\[(\s*\d{1,3}(?:\s*[-–—]\s*\d{1,3})?(?:\s*[,;]\s*\d{1,3}(?:\s*[-–—]\s*\d{1,3})?)*\s*)\](?![\](])"
)
SURNAME = r"(?:(?:de|del|de la|van|van der|von|da|di|le)\s+)?[A-ZÀ-ÖØ-Þ][\w'’\-]+"
AUTHORS = (
    rf"{SURNAME}(?:\s+(?:et al\.?|and colleagues|y col(?:s)?\.?)"
    rf"|\s*(?:&|and|y|und|e)\s+{SURNAME}"
    rf"|(?:,\s*{SURNAME})*,?\s*(?:&|and|y)\s+{SURNAME})?"
)
YEAR = r"(?:19|20)\d{2}[a-z]?|n\.d\.|s\.f\.|in press|en prensa"
# (Smith et al., 2020; Jones & Lee, 2019a) and (see Smith, 2020, p. 4)
PAREN_GROUP = re.compile(r"\(([^()]*?(?:19|20)\d{2}[a-z]?[^()]*?)\)")
PAREN_ITEM = re.compile(rf"({AUTHORS}),?\s+({YEAR})")
# Smith et al. (2020)
NARRATIVE = re.compile(rf"({AUTHORS})\s+\(({YEAR})(?:[,;][^)]*)?\)")


@dataclass(frozen=True)
class Citation:
    kind: str  # "numeric" | "author_year"
    labels: tuple[str, ...]  # numeric labels, or "surname|year" keys
    start: int
    end: int
    text: str


def expand_numeric(spec: str) -> list[str]:
    out: list[str] = []
    for part in re.split(r"[,;]", spec):
        part = part.strip()
        if not part:
            continue
        m = re.match(r"(\d+)\s*[-–—]\s*(\d+)$", part)
        if m:
            a, b = int(m.group(1)), int(m.group(2))
            if a <= b and b - a <= 50:
                out.extend(str(n) for n in range(a, b + 1))
                continue
        out.append(part)
    return out


def author_year_key(authors: str, year: str) -> str:
    first = re.split(r"\s+(?:et al\b|and\b|&|y\b|und\b|e\b)|,", authors.strip())[0]
    first = re.sub(r"^(?:de la|de|del|van der|van|von|da|di|le)\s+", "", first.strip(), flags=re.I)
    return f"{first.casefold()}|{year.casefold()}"


def find_citations(text: str) -> list[Citation]:
    found: list[Citation] = []
    for m in NUMERIC.finditer(text):
        found.append(
            Citation("numeric", tuple(expand_numeric(m.group(1))), m.start(), m.end(), m.group(0))
        )
    for m in PAREN_GROUP.finditer(text):
        keys = tuple(author_year_key(a, y) for a, y in PAREN_ITEM.findall(m.group(1)))
        if keys:
            found.append(Citation("author_year", keys, m.start(), m.end(), m.group(0)))
    for m in NARRATIVE.finditer(text):
        if any(c.start <= m.start(2) < c.end for c in found):
            continue
        found.append(
            Citation(
                "author_year",
                (author_year_key(m.group(1), m.group(2)),),
                m.start(),
                m.end(),
                m.group(0),
            )
        )
    return sorted(found, key=lambda c: c.start)


_SENTENCE_END = re.compile(
    r"(?<!\bet al)(?<!\be\.g)(?<!\bi\.e)(?<!\bvs)(?<!\bFig)(?<!\bp)(?<!\bpp)(?<!\bNo)(?<!\bca)"
    r"(?<=[.!?])\s+(?=[A-ZÀ-ÖØ-Þ¿¡\[(])"
)


def split_sentences(text: str) -> list[tuple[int, int, str]]:
    """Split prose into (start, end, sentence); paragraph and list-item breaks always split."""
    spans: list[tuple[int, int, str]] = []
    for block in re.finditer(r"[^\n]+(?:\n(?![\s]*\n|\s*(?:[-*+]|\d+[.)])\s)[^\n]+)*", text):
        offset = block.start()
        chunk = block.group(0)
        pos = 0
        for m in _SENTENCE_END.finditer(chunk):
            spans.append((offset + pos, offset + m.start(), chunk[pos : m.start()].strip()))
            pos = m.end()
        spans.append((offset + pos, offset + len(chunk), chunk[pos:].strip()))
    return [s for s in spans if s[2]]


@dataclass(frozen=True)
class CitingSentence:
    sentence: str
    citations: tuple[Citation, ...]


def citing_sentences(text: str) -> list[CitingSentence]:
    cites = find_citations(text)
    out = []
    for start, end, sentence in split_sentences(text):
        inside = tuple(c for c in cites if start <= c.start < end)
        if inside:
            out.append(CitingSentence(sentence, inside))
    return out
