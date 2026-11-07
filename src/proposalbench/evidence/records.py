from __future__ import annotations

import re
from dataclasses import dataclass, field
from html import unescape
from typing import Any, Literal

from proposalbench.parse.references import normalize_doi

Source = Literal["crossref", "datacite", "openalex", "semanticscholar", "arxiv", "exa", "url"]


@dataclass(frozen=True)
class WorkRecord:
    source: Source
    id: str
    doi: str | None = None
    title: str | None = None
    authors: list[str] = field(default_factory=list)
    year: int | None = None
    venue: str | None = None
    kind: str = "other"
    url: str | None = None
    abstract: str | None = None
    raw_ref: dict[str, Any] = field(default_factory=dict)


def plain_text(value: str | None) -> str | None:
    return re.sub(r"\s+", " ", unescape(re.sub("<[^>]+>", " ", value))).strip() if value else None


def family_name(name: str) -> str:
    if "," in name:
        return name.split(",")[0].strip()
    parts = name.split()
    start = len(parts) - 1
    while start > 0 and parts[start - 1].lower() in {"de", "del", "van", "von", "der", "la"}:
        start -= 1
    return " ".join(parts[start:])


def first(value: Any) -> Any:
    return (value[0] if value else None) if isinstance(value, list) else value


def _csl_title(data: dict) -> str | None:
    """Title with its CSL subtitle: books and proceedings often keep the subtitle apart."""
    title = plain_text(first(data.get("title")))
    subtitle = plain_text(first(data.get("subtitle")))
    if title and subtitle and " ".join(subtitle.split()).casefold() not in title.casefold():
        return f"{title}: {subtitle}"
    return title


def _csl_year(data: dict) -> int | None:
    """First usable year among the CSL dates; Crossref sometimes sends date-parts [[null]]."""
    for key in ("published", "issued", "published-print", "published-online", "created"):
        parts = (data.get(key) or {}).get("date-parts") or [[]]
        value = parts[0][0] if parts and parts[0] else None
        try:
            return int(value)
        except (TypeError, ValueError):
            continue
    return None


def from_csl(data: dict, source: Source = "crossref") -> WorkRecord:
    kind = {
        "article-journal": "journal_article",
        "journal-article": "journal_article",
        "book-chapter": "chapter",
        "posted-content": "preprint",
    }.get(data.get("type"), data.get("type", "other"))
    doi = normalize_doi(data.get("DOI"))
    return WorkRecord(
        source,
        doi or str(data.get("id", "")),
        doi,
        _csl_title(data),
        [
            a.get("family") or a.get("literal") or family_name(a.get("name", ""))
            for a in data.get("author", [])
            if a.get("family") or a.get("literal") or a.get("name")
        ],
        _csl_year(data),
        first(data.get("container-title")) or data.get("publisher"),
        kind,
        data.get("URL") or data.get("url"),
        plain_text(data.get("abstract")),
        {k: data[k] for k in ("DOI", "title", "type", "publisher") if k in data},
    )
