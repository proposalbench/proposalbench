from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Literal

from rapidfuzz import fuzz

from proposalbench.evidence.records import family_name

AuthorMatch = Literal["first", "some", "none", "unknown"]


@dataclass(frozen=True)
class MatchConfig:
    title_ok: float = 92
    dossier_ok: float = 90
    dossier_possible: float = 75
    doi_unrelated: float = 60
    venue_different: float = 45
    year_tolerance: int = 1
    misattributed_min_authors: int = 2
    # A title-search hit can only prove misattribution when the title is specific: short
    # titles (or a journal name parsed as a title) match unrelated records.
    misattributed_min_title_words: int = 5
    # A resolved work whose title occurs in the raw reference text is the cited work even when
    # parsing split the reference wrongly; only titles this long count as evidence.
    raw_title_partial: float = 95
    raw_title_min_words: int = 4
    indexable_since: int = 2000


def normalize_title(title: str | None) -> str:
    decomposed = unicodedata.normalize("NFKD", (title or "").casefold())
    plain = "".join(c for c in decomposed if not unicodedata.combining(c))
    return " ".join(re.sub(r"[^\w\s]|_", " ", plain).split())


def title_similarity(left: str | None, right: str | None) -> float:
    """Keep ordered ratio, or 80% token-sort + 20% ordered ratio for reordered titles.

    Unlike token-set matching, extra subtitle words are penalized. Retaining an
    ordered component prevents identical word bags from being automatic exact matches.
    """
    a, b = normalize_title(left), normalize_title(right)
    if not a or not b:
        return 0.0
    ordered = fuzz.ratio(a, b)
    return max(ordered, 0.8 * fuzz.token_sort_ratio(a, b) + 0.2 * ordered)


def author_overlap(cited: list[str], found: list[str]) -> AuthorMatch:
    if not cited or not found:
        return "unknown"
    a = [normalize_title(family_name(x)) for x in cited]
    b = [normalize_title(family_name(x)) for x in found]
    if _same_family(a[0], b[0]):
        return "first"
    return "some" if any(_same_family(x, y) for x in a for y in b) else "none"


def _same_family(a: str, b: str) -> bool:
    """Equal family names, or one is the last part of the other: a compound surname written
    without initials ("Recuero Valdelomar") is read as its last word."""
    if not a or not b:
        return False
    return a == b or a.endswith(" " + b) or b.endswith(" " + a)


def venue_disagrees(cited: str | None, found: str | None, cfg: MatchConfig) -> bool:
    if not cited or not found:
        return False
    a, b = normalize_title(cited), normalize_title(found)
    if a in b or b in a or title_similarity(a, b) >= cfg.venue_different:
        return False
    a_words, b_words = a.split(), b.split()
    if any(len(x) <= 3 for x in a_words + b_words):
        return False
    return not any(x.startswith(y) or y.startswith(x) for x in a_words for y in b_words)


def raw_mentions_title(raw: str, title: str | None, cfg: MatchConfig) -> bool:
    """Whether a work's title occurs in the raw reference text, independent of parsing."""
    t, r = normalize_title(title), normalize_title(raw)
    if len(t.split()) < cfg.raw_title_min_words or not r:
        return False
    return fuzz.partial_ratio(t, r) >= cfg.raw_title_partial


def authors_are_title(authors: list[str], title: str | None, cfg: MatchConfig) -> bool:
    """Whether a parsed author list is in fact the work's title.

    An author-less reference ("Title. (Year). Retrieved from https://doi.org/...") puts its
    title where authors usually stand, and the parser reads it as authors.
    """
    cited = normalize_title(" ".join(authors)).split()
    words = normalize_title(title).split()
    if len(words) < cfg.raw_title_min_words or not cited:
        return False
    title_covered = sum(w in cited for w in words) / len(words)
    nothing_else = sum(w in words for w in cited) / len(cited)
    return title_covered >= 0.8 and nothing_else >= 0.9


def raw_mentions_authors(raw: str, authors: list[str]) -> bool:
    """Whether one of the work's first three family names occurs in the raw reference text."""
    words = set(normalize_title(raw).split())
    names = [normalize_title(family_name(a)).split() for a in authors[:3]]
    return any(n and all(part in words for part in n) for n in names)


def main_title_match(cited: str | None, found: str | None) -> bool:
    """Whether one title is the other without its subtitle, in either direction.

    "DART: directed automated random testing" is the work whose record title is "DART", and
    a citation of "Garbage matters" names the record "Garbage matters: Concepts in ...".
    """

    def main(title: str | None) -> str | None:
        parts = re.split(r"\s*[:–—?]\s+|\s+-\s+|\.\s+", title or "", maxsplit=1)
        return normalize_title(parts[0]) if len(parts) == 2 else None

    a, b = normalize_title(cited), normalize_title(found)
    return bool(a and b) and (main(cited) == b or main(found) == a)
