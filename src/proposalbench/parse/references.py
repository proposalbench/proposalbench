from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal
from urllib.parse import unquote

Kind = Literal[
    "journal_article", "book", "chapter", "report", "preprint", "web", "dataset", "other"
]
# "]" ends a DOI: Markdown links write "[https://doi.org/X](https://doi.org/X)".
DOI_RE = re.compile(r'10\.\d{4,9}/[^\s<>"|\]]+', re.I)
YEAR_RE = re.compile(r"\b((?:18|19|20)\d{2})[a-z]?\b")
MARKER_RE = re.compile(r"^\s*(?:\[(\d+)\]|(\d+)[.)]|[-*+])\s+")


@dataclass(frozen=True)
class ParsedReference:
    index: int
    label: str | None
    raw: str
    doi: str | None = None
    arxiv_id: str | None = None
    url: str | None = None
    year: int | None = None
    title: str | None = None
    authors: list[str] = field(default_factory=list)
    venue: str | None = None
    kind_guess: Kind = "other"
    parse_confidence: float = 0.0


def normalize_doi(value: str | None) -> str | None:
    if not value:
        return None
    match = DOI_RE.search(unquote(value))
    if not match:
        return None
    doi = match[0].rstrip(".,;:!?'”’*")
    for opening, closing in [("(", ")"), ("[", "]"), ("{", "}")]:
        while doi.endswith(closing) and doi.count(closing) > doi.count(opening):
            doi = doi[:-1]
    return doi.lower()


def surnames(value: str) -> list[str]:
    """Extract family names from initials-first, inverted and Vancouver author lists."""
    value = re.sub(r"\bet\s+al\.?", "", value, flags=re.I)
    # Chicago commonly spells out the given name after the family-name comma.
    value = re.sub(
        r"^([\w’' -]+),\s+[A-ZÁÉÍÓÚ][a-záéíóú]+(?:\s+[A-Z][a-z]+)*\.?"
        r"(?=\s*(?:$|;|,?\s+(?:and|y|&)))",
        r"\1",
        value.strip(" .()"),
    )
    value = re.sub(r"\b(?:and|y)\b|&|;", ",", value)
    names = []
    for part in value.split(","):
        part = part.strip(" .()")
        if not part or (
            re.fullmatch(r"(?:[A-ZÁÉÍÓÚ]\.?\s*)+", part) and (len(part) <= 2 or "." in part)
        ):
            continue
        part = re.sub(r"^(?:[A-ZÁÉÍÓÚ]\.\s*)+", "", part)
        part = re.sub(r"\s+(?:[A-ZÁÉÍÓÚ]\.?\s*)+$", "", part).strip()
        if part and part.casefold() not in {"unknown", "anonymous", "desconocido"}:
            names.append(part)
    return names


VANCOUVER_AUTHOR = r"[^\W\d][\w'’\- ]*?\s[A-Z]{1,3}(?:-[A-Z])?"
VANCOUVER_RE = re.compile(
    rf"^(?P<authors>{VANCOUVER_AUTHOR}(?:,\s*{VANCOUVER_AUTHOR})*(?:,\s*et al)?)\.\s+(?P<rest>.+)$"
)


# Pensoft/RIO: "Crawford D. J., Mort M. E. 2005. Title. Journal. 92. 2. 330. 336."
PENSOFT_AUTHOR = r"[^\W\d][\w'’\-]*(?:\s[^\W\d][\w'’\-]*)*\s(?:[A-Z]\.\s?)+"
PENSOFT_RE = re.compile(
    rf"^(?P<authors>{PENSOFT_AUTHOR}(?:,\s*{PENSOFT_AUTHOR})*(?:,?\s*et al\.)?)\s*"
    r"\(?(?P<year>(?:18|19|20)\d{2}[a-z]?)\)?\.\s+(?P<rest>.+)$"
)


def _clean(text: str) -> str:
    # Inline emphasis (*Staphylococcus aureus*, _S. aureus_) is presentation, not title text.
    text = re.sub(r"(\*{1,2}|_{1,2})(?=\S)(.+?)(?<=\S)\1", r"\2", text)
    return text.strip(' \t\n.*_"“”‘’')


def _metadata(text: str) -> tuple[str | None, list[str], str | None]:
    text = re.sub(r"\[([^\]]+)\]\(https?://[^)]+\)", r"\1", text)
    text = re.sub(r"https?://\S+|(?:doi\s*:\s*)?10\.\d{4,9}/\S+", "", text, flags=re.I)
    text = re.sub(r"\b(?:Retrieved from|Recuperado de|Available at)\b.*", "", text, flags=re.I)
    quoted = (
        re.search(r'[“"‘«](.+?)[”"’»]', text)
        # Straight single quotes around a title ('Title.' Journal): opening after a space or
        # bracket, closing before a space or punctuation, so apostrophes (O'Brien) do not count.
        or re.search(r"(?:(?<=[\s(])|^)'([^'\n]{8,}?)'(?=[\s.,;:]|$)", text)
    )
    year = re.search(r"\(?\b(?:18|19|20)\d{2}[a-z]?\)?[.,]?\s+", text)
    vancouver = VANCOUVER_RE.match(text)
    pensoft = PENSOFT_RE.match(text)
    # A year near the start separates APA/Harvard authors from the title.
    if pensoft:
        author_text = pensoft["authors"]
        pieces = re.split(r"(?<=[^A-Z])[.?!]\s+", pensoft["rest"], maxsplit=1)
        title = _clean(pieces[0])
        tail = pieces[1] if len(pieces) > 1 else ""
    elif vancouver and not quoted:
        # Vancouver/ICMJE: "Surname AB, Surname C, et al. Title. Journal. 2019;17(7):441."
        author_text = vancouver["authors"]
        # Hybrid "Surname AB, Surname C. (2011). Title. Journal." puts the year first.
        rest = re.sub(r"^\(?(?:18|19|20)\d{2}[a-z]?\)?[.,]?\s+", "", vancouver["rest"])
        pieces = re.split(r"(?<=[^A-Z])[.?!]\s+", rest, maxsplit=1)
        title = _clean(pieces[0])
        tail = pieces[1] if len(pieces) > 1 else ""
    elif quoted:
        title = _clean(quoted[1])
        author_text = text[: quoted.start()]
        tail = text[quoted.end() :].lstrip(" .,")
    elif (
        year
        and year.start() < len(text) * 0.65
        and not re.search(r"(?<!\b[A-Z])\.\s+[A-Z][a-z]{2}", text[: year.start()])
    ):
        author_text = text[: year.start()]
        tail = text[year.end() :].lstrip(" .")
        pieces = re.split(r"\.\s+|\s*\|\s*", tail, maxsplit=1)
        title = _clean(pieces[0])
        tail = pieces[1] if len(pieces) > 1 else ""
    else:
        # Initials and "et al." are not sentence boundaries.
        protected = re.sub(r"\b([A-Z])\.", lambda m: m[1] + "\x00", text)
        protected = re.sub(r"\bet al\.", "et al\x00", protected, flags=re.I)
        pieces = re.split(r"\.\s+|\s*\|\s*", protected, maxsplit=2)
        pieces = [p.replace("\x00", ".") for p in pieces]
        if len(pieces) >= 2:
            author_text, title = pieces[:2]
            tail = pieces[2] if len(pieces) > 2 else ""
            title = _clean(title)
        else:
            author_text, tail = "", ""
            title = _clean(text)
    author_text = YEAR_RE.sub("", author_text)
    authors = surnames(author_text)
    venue = re.split(r"\.\s+|[,;]\s*\d|\b(?:18|19|20)\d{2}\b", tail)[0]
    venue = _clean(venue).strip(" ,;:()") or None
    if venue and re.match(r"^(?:doi|arxiv|retrieved|https?\b)", venue, re.I):
        venue = None
    if not title or len(title.split()) < 2 or re.fullmatch(r"[\W\d_]+", title):
        title = None
    return title, authors, venue


def _parse(index: int, label: str | None, raw: str) -> ParsedReference:
    text = " ".join(raw.split())
    doi = normalize_doi(text)
    url_match = re.search(r"https?://[^\s<>\]]+", text)
    url = url_match[0].rstrip(".,;:)]") if url_match else None
    arxiv = re.search(
        r"(?:arxiv\s*:\s*|arxiv\.org/(?:abs|pdf)/)"
        r"((?:\d{4}\.\d{4,5}|[a-z.-]+/\d{7})(?:v\d+)?)",
        text,
        re.I,
    )
    year_match = YEAR_RE.search(re.sub(r"https?://\S+|10\.\d{4,9}/\S+", "", text))
    year = int(year_match[1]) if year_match else None
    title, authors, venue = _metadata(text)
    lower = text.casefold()
    kind: Kind = "other"
    if arxiv or re.search(r"\b(?:preprint|arxiv|biorxiv|medrxiv)\b", lower):
        kind = "preprint"
    elif re.search(r"\b(?:dataset|data set|conjunto de datos)\b", lower):
        kind = "dataset"
    elif re.search(r"\b(?:report|informe|world health organization|who)\b", lower):
        kind = "report"
    elif re.search(r"\b(?:in|en)\s+.+(?:eds?\.|pp\.)", text, re.I):
        kind = "chapter"
    elif re.search(r"\b(?:press|publisher|editorial|isbn|springer|routledge|wiley)\b", lower):
        kind = "book"
    elif venue or re.search(r"\b(?:journal|revista)\b|\d+\s*\(\d+\)", lower):
        kind = "journal_article"
    elif url:
        kind = "web"
    confidence = min(
        1.0,
        0.35 * bool(title)
        + 0.2 * bool(authors)
        + 0.15 * bool(year)
        + 0.2 * bool(doi or arxiv or url)
        + 0.1 * bool(venue),
    )
    return ParsedReference(
        index,
        label,
        raw,
        doi,
        arxiv[1] if arxiv else None,
        url,
        year,
        title,
        authors,
        venue,
        kind,
        confidence,
    )


HRULE_RE = re.compile(r"^\s*(?:-{3,}|\*{3,}|_{3,})\s*$", re.M)


def parse_references(block: str) -> list[ParsedReference]:
    # A horizontal rule ends the reference list; what follows is a note, not a reference.
    if m := HRULE_RE.search(block):
        block = block[: m.start()]
    entries: list[tuple[str | None, list[str]]] = []
    current: list[str] = []
    label = None
    numbered = bool(re.search(r"^\s*(?:\[\d+\]|\d+[.)]|[-*+])\s+", block, re.M))
    for line in block.splitlines():
        marker = MARKER_RE.match(line)
        if marker or (not line.strip() and not numbered):
            if current:
                entries.append((label, current))
                current = []
            label = (marker[1] or marker[2]) if marker else None
        if line.strip():
            current.append(line[marker.end() :].strip() if marker else line.strip())
    if current:
        entries.append((label, current))
    return [_parse(i, label, "\n".join(lines)) for i, (label, lines) in enumerate(entries)]
