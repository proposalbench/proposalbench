"""Deterministic validation of the task set (no network).

Schema errors surface when loading. These checks cover what the schema cannot: that annotations
agree with the Markdown the systems read, that canaries are present, that splits are disjoint and
that no long passage was copied from a seed document.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from pydantic import ValidationError

from proposalbench.checks.admissibility import detect_language
from proposalbench.parse.sections import WORD, normalize_heading
from proposalbench.tasks.loader import Repository, ResolvedTask
from proposalbench.tasks.schema import CANARY_RE, Split, Task

NGRAM = 12


@dataclass(frozen=True)
class Problem:
    where: str
    message: str
    severity: str = "error"  # "error" | "warning"


def _norm_number(s: str) -> list[str]:
    """Spellings of a number as it may appear in Markdown (1200, 1,200, 1 200, 0.31)."""
    s = s.strip()
    out = {s}
    if re.fullmatch(r"\d+(\.\d+)?", s):
        intpart, _, frac = s.partition(".")
        if len(intpart) > 3:
            grouped = f"{int(intpart):,}"
            out |= {grouped + (f".{frac}" if frac else ""), grouped.replace(",", " ")}
        if s.endswith(".0"):
            out.add(intpart)
    return sorted(out)


def _value_variants(value: object) -> list[str]:
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    parts = [p.strip() for p in str(value).split(";")]
    variants: list[str] = []
    for p in parts:
        variants.extend(_norm_number(p))
    return variants


# A cited web address is a reference, not copied prose.
_URL = re.compile(r"(?:https?://|www\.)\S+")


def _ngrams(text: str, n: int = NGRAM) -> set[tuple[str, ...]]:
    words = [w.casefold() for w in WORD.findall(_URL.sub(" ", text))]
    return {tuple(words[i : i + n]) for i in range(len(words) - n + 1)}


def check_task(rt: ResolvedTask) -> list[Problem]:
    problems: list[Problem] = []
    where = rt.id
    try:
        Task.model_validate(rt.task.model_dump(), context={"call": rt.call, "dossier": rt.dossier})
    except ValidationError as exc:
        problems.append(Problem(where, f"inconsistent task type: {exc}"))

    for name, canary in (
        ("task", rt.task.canary),
        ("call", rt.call.canary),
        ("dossier", rt.dossier.canary),
    ):
        if not CANARY_RE.match(canary):
            problems.append(Problem(where, f"{name} canary is malformed: {canary!r}"))
    if rt.call.canary not in rt.call_text:
        problems.append(Problem(where, "call.md does not carry the call's canary comment"))

    lc = rt.call.length_contract
    stated = {f"{lc.max_words:,}", str(lc.max_words), f"{lc.max_words:,}".replace(",", ".")}
    if not any(s in rt.call_text for s in stated):
        problems.append(Problem(where, f"call.md never states the binding limit of {lc.max_words}"))
    if lc.page_limit and lc.words_per_page:
        implied = lc.page_limit * lc.words_per_page
        if abs(implied - lc.max_words) / lc.max_words > 0.1:
            problems.append(
                Problem(
                    where, f"max_words {lc.max_words} far from pages x words/page {implied:.0f}"
                )
            )

    headings = normalize_heading(rt.call_text)
    for s in rt.call.required_sections:
        if normalize_heading(s.title) not in headings:
            problems.append(
                Problem(
                    where, f"required section {s.id} '{s.title}' not named in call.md", "warning"
                )
            )

    texts = rt.dossier_texts()
    for fact in rt.dossier.facts:
        if fact.value is None:
            continue
        src = texts[fact.source]
        if not any(v in src for v in _value_variants(fact.value)):
            problems.append(
                Problem(where, f"fact {fact.id} value {fact.value!r} not found in {fact.source}")
            )
    all_dossier = normalize_heading("\n".join(texts.values()))
    for pub in rt.dossier.own_publications:
        if normalize_heading(pub.title) not in all_dossier:
            problems.append(Problem(where, f"own publication {pub.key} title not in dossier files"))
        if pub.doi and pub.doi not in "\n".join(texts.values()):
            problems.append(Problem(where, f"own publication {pub.key} DOI not in dossier files"))

    for label, text, lang in [("call.md", rt.call_text, rt.call.language)] + [
        (p, t, rt.dossier.language) for p, t in texts.items()
    ]:
        detected, conf = detect_language(text)
        if detected and detected != lang and conf > 0.6:
            problems.append(Problem(where, f"{label} looks like {detected!r}, expected {lang!r}"))

    if rt.task.brief and rt.brief_text is None:
        problems.append(Problem(where, f"brief {rt.task.brief} missing"))

    # A trap that quotes the material must quote what the system receives: revisions of a
    # dossier or brief after the task was written can leave a stale quotation behind.
    received = _quote_norm("\n".join([rt.call_text, *texts.values(), rt.brief_text or ""]))
    for trap in rt.task.traps:
        for quoted in _quoted_pieces(trap.description):
            if _quote_norm(quoted) not in received:
                problems.append(
                    Problem(where, f"trap {trap.id} quotes text not in the bundle: {quoted[:80]!r}")
                )
    return problems


_QUOTES = str.maketrans({"\u201c": '"', "\u201d": '"', "\u00ab": '"', "\u00bb": '"'})


def _quote_norm(text: str) -> str:
    # One quote mark for all: a faithful quotation turns the source's double quotes into
    # single ones ("called 'X'" for a source reading called "X").
    text = re.sub(r"[*_`>]", "", text).replace("\u2019", "'").replace("\u2018", "'")
    # A table row quoted as prose ("Unit established: no" for "| Unit established | no |").
    text = re.sub(r"\s*[|:]\s*", " ", text)
    return " ".join(text.translate(_QUOTES).replace('"', "'").split()).casefold()


# A single-quoted passage opens and closes on a quote mark outside a word, so apostrophes
# inside words ("PI's", "didn't") do not end it.
_SINGLE_QUOTED = re.compile(r"(?<![\w'])'((?:[^'\n]|(?<=\w)'(?=\w))+?)'(?![\w])")


def _quoted_pieces(description: str, min_chars: int = 20) -> list[str]:
    """Quoted passages of a trap description, in double or single quotation marks, split at
    elisions ("...", "[...]")."""
    out = []
    text = description.translate(_QUOTES).replace("\u2019", "'").replace("\u2018", "'")
    doubles = re.findall(r'"([^"]*)"', text)
    singles = _SINGLE_QUOTED.findall(re.sub(r'"[^"]*"', " ", text))
    for quoted in doubles + singles:
        for piece in re.split(r"\.\.\.|\u2026|\[[^\]]*\]", quoted):
            piece = piece.strip(" .,;:")
            if len(piece) >= min_chars:
                out.append(piece)
    return out


def _boilerplate_grams(path: Path) -> set[tuple[str, ...]]:
    if not path.is_file():
        return set()
    grams: set[tuple[str, ...]] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.startswith("#"):
            grams |= _ngrams(line)
    return grams


def check_seed_overlap(
    rt: ResolvedTask, seeds_dir: Path, boilerplate: Path | None = None
) -> list[Problem]:
    if not seeds_dir.is_dir():
        return []
    allowed = _boilerplate_grams(boilerplate) if boilerplate else set()
    task_grams = _ngrams(rt.call_text)
    for t in rt.dossier_texts().values():
        task_grams |= _ngrams(t)
    if rt.brief_text:
        task_grams |= _ngrams(rt.brief_text)
    problems = []
    for seed in sorted(seeds_dir.rglob("*.md")):
        shared = (task_grams & _ngrams(seed.read_text(encoding="utf-8"))) - allowed
        if shared:
            example = " ".join(next(iter(shared)))
            problems.append(
                Problem(
                    rt.id, f"shares {len(shared)} {NGRAM}-grams with seed {seed.name}: '{example}'"
                )
            )
    return problems


def validate_repository(repo: Repository, seeds_dir: Path | None = None) -> list[Problem]:
    problems: list[Problem] = []
    resolved: list[ResolvedTask] = []
    for d in repo.task_dirs():
        try:
            resolved.append(repo.load_task(d))
        except (ValidationError, ValueError, FileNotFoundError) as exc:
            problems.append(Problem(d.name, f"cannot load: {exc}"))

    ids = Counter(rt.id for rt in resolved)
    problems += [Problem(i, "duplicate task id") for i, n in ids.items() if n > 1]

    by_split: dict[Split, list[ResolvedTask]] = {}
    for rt in resolved:
        by_split.setdefault(rt.task.split, []).append(rt)
        problems += check_task(rt)
        if seeds_dir is not None:
            problems += check_seed_overlap(rt, seeds_dir, repo.root / "seeds" / "boilerplate.txt")

    pub = by_split.get(Split.public, [])
    for kind, key in (("call", lambda r: r.call.id), ("dossier", lambda r: r.dossier.id)):
        for item, n in Counter(key(r) for r in pub).items():
            if n > 2:
                problems.append(Problem(item, f"public {kind} used by {n} tasks (max 2)"))
        sealed = {key(r) for r in by_split.get(Split.sealed, [])}
        for item in sealed & {key(r) for r in pub}:
            problems.append(Problem(item, f"{kind} appears in both public and sealed splits"))
    return problems
