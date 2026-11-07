"""Style diagnostics: rates of patterns typical of machine-written prose.

These numbers are reported next to the score and compared with human-written proposals; they
never enter the score. Every pattern has legitimate uses, and a system tuned against these lists
would beat them without writing a better proposal.
"""

from __future__ import annotations

import csv
import re
from collections import Counter
from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np

from proposalbench.parse.citations import split_sentences
from proposalbench.parse.sections import WORD, ParsedProposal, strip_markdown

LEXICONS = Path(__file__).resolve().parents[3] / "lexicons"

NOT_ONLY = {
    "en": re.compile(r"\bnot only\b[^.;:!?]{1,200}?\bbut(?: also)?\b", re.I),
    "es": re.compile(r"\bno solo\b[^.;:!?]{1,200}?\bsino(?: también)?\b", re.I),
}
GERUND_OPENER = {
    "en": re.compile(r"^(?:By|Through)\s+\w+ing\b"),
    "es": re.compile(r"^(?:Mediante|A través de)\s+(?:la|el|los|las)\s+\w+", re.I),
}
BULLET = re.compile(r"^\s*(?:[-*+•]|\d+[.)])\s+")


@dataclass(frozen=True)
class StyleProfile:
    language: str
    words: int
    sentences: int
    mean_sentence_words: float
    sentence_length_cv: float
    buzzwords_per_1k: float
    excess_style_words_per_1k: float | None  # Kobak et al. list; English only
    em_dashes_per_1k: float
    not_only_but_per_1k: float
    gerund_openers_per_100_sentences: float
    bullet_line_share: float
    repeated_4gram_share: float
    top_buzzwords: dict[str, int]

    def to_dict(self) -> dict:
        return asdict(self)


@lru_cache(maxsize=4)
def _buzzword_patterns(language: str) -> list[tuple[str, re.Pattern[str]]]:
    path = LEXICONS / f"grant_buzzwords_{language}.txt"
    if not path.is_file():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        entry = line.strip()
        if not entry or entry.startswith("#"):
            continue
        body = r"\s+".join(
            re.escape(w[:-1]) + r"\w*" if w.endswith("*") else re.escape(w) for w in entry.split()
        )
        out.append((entry, re.compile(rf"(?<!\w){body}(?!\w)", re.I)))
    return out


@lru_cache(maxsize=1)
def _kobak_style_words() -> frozenset[str]:
    path = LEXICONS / "kobak_excess_words.csv"
    with path.open(encoding="utf-8") as fh:
        return frozenset(r["word"] for r in csv.DictReader(fh) if r["type"].startswith("style"))


def _per(n: int, d: int, scale: int) -> float:
    return round(n * scale / d, 3) if d else 0.0


def style_profile(parsed: ParsedProposal, language: str) -> StyleProfile:
    raw = parsed.body_text()
    text = strip_markdown(raw)
    words = [w.casefold() for w in WORD.findall(text)]
    n = len(words)
    prose = "\n".join(line for line in raw.splitlines() if not line.lstrip().startswith("|"))
    sentences = [s for _, _, s in split_sentences(strip_markdown(prose))]
    lengths = np.array([len(WORD.findall(s)) for s in sentences if WORD.search(s)], dtype=float)

    buzz = Counter()
    for entry, pat in _buzzword_patterns(language):
        hits = len(pat.findall(text))
        if hits:
            buzz[entry] = hits
    if language == "en":
        kobak = _kobak_style_words()
        excess: float | None = _per(sum(1 for w in words if w in kobak), n, 1000)
    else:
        excess = None

    not_only = NOT_ONLY.get(language)
    gerund = GERUND_OPENER.get(language)
    lines = [ln for ln in raw.splitlines() if ln.strip() and not ln.lstrip().startswith("|")]
    grams = Counter(tuple(words[i : i + 4]) for i in range(max(0, n - 3)))
    repeated = sum(c - 1 for c in grams.values() if c > 2)

    return StyleProfile(
        language=language,
        words=n,
        sentences=len(sentences),
        mean_sentence_words=round(float(lengths.mean()), 2) if lengths.size else 0.0,
        sentence_length_cv=round(float(lengths.std() / lengths.mean()), 3) if lengths.size else 0.0,
        buzzwords_per_1k=_per(sum(buzz.values()), n, 1000),
        excess_style_words_per_1k=excess,
        em_dashes_per_1k=_per(raw.count("—"), n, 1000),
        not_only_but_per_1k=_per(len(not_only.findall(text)) if not_only else 0, n, 1000),
        gerund_openers_per_100_sentences=_per(
            sum(1 for s in sentences if gerund and gerund.match(s.strip())), len(sentences), 100
        ),
        bullet_line_share=round(sum(1 for ln in lines if BULLET.match(ln)) / len(lines), 3)
        if lines
        else 0.0,
        repeated_4gram_share=round(repeated / max(1, n - 3), 4),
        top_buzzwords=dict(buzz.most_common(10)),
    )
