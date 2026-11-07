from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any
from xml.etree.ElementTree import ParseError

import httpx

from proposalbench.evidence.http import EvidenceClient, OfflineCacheMiss
from proposalbench.evidence.match import (
    AuthorMatch,
    MatchConfig,
    author_overlap,
    authors_are_title,
    main_title_match,
    raw_mentions_authors,
    raw_mentions_title,
    title_similarity,
    venue_disagrees,
)
from proposalbench.evidence.records import WorkRecord
from proposalbench.evidence.resolvers import (
    arxiv,
    crossref,
    doi,
    exa,
    openalex,
    semanticscholar,
    url,
)
from proposalbench.parse.references import ParsedReference, normalize_doi
from proposalbench.tasks.schema import FICTIONAL_DOI_REGISTRANT, OwnPublication


class RefStatus(StrEnum):
    DOSSIER = "dossier"
    DOSSIER_MISCITED = "dossier_miscited"
    VERIFIED = "verified"
    VERIFIED_WITH_ERRORS = "verified_with_errors"
    MISATTRIBUTED = "misattributed"
    DOI_UNRESOLVED = "doi_unresolved"
    NOT_FOUND = "not_found"
    UNPARSEABLE = "unparseable"


@dataclass(frozen=True)
class ReferenceVerdict:
    ref: ParsedReference
    status: RefStatus
    indexable: bool
    best: WorkRecord | None = None
    title_score: float = 0.0
    author_match: AuthorMatch = "unknown"
    year_delta: int | None = None
    checked_sources: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def _dossier(
    ref: ParsedReference,
    pubs: Sequence[Mapping[str, Any] | OwnPublication],
    cfg: MatchConfig,
    indexable: bool,
) -> ReferenceVerdict | None:
    reserved = bool(ref.doi and ref.doi.startswith(FICTIONAL_DOI_REGISTRANT))
    candidates = []
    for pub in pubs:
        data = pub.model_dump() if isinstance(pub, OwnPublication) else dict(pub)
        score = title_similarity(ref.title, data.get("title"))
        exact_doi = bool(reserved and ref.doi == normalize_doi(data.get("doi")))
        candidates.append((exact_doi, score, data))
    if candidates:
        exact, score, data = max(candidates, key=lambda x: (x[0], x[1]))
        if exact or score >= cfg.dossier_possible:
            authors = author_overlap(ref.authors, data.get("authors", []))
            delta = ref.year - data["year"] if ref.year and data.get("year") else None
            notes = []
            if delta is not None and delta != 0:
                notes.append("year_mismatch")
            if authors == "none":
                notes.append("authors_mismatch")
            if venue_disagrees(ref.venue, data.get("venue"), cfg):
                notes.append("venue_mismatch")
            if exact and ref.title and score < cfg.dossier_ok:
                notes.append("title_mismatch")
            if reserved and not exact:
                notes.append("unknown_dossier_doi")
            if exact or score >= cfg.dossier_ok or notes:
                # A dossier item is fictional, so it is never an external WorkRecord.
                return ReferenceVerdict(
                    ref,
                    RefStatus.DOSSIER_MISCITED if notes else RefStatus.DOSSIER,
                    indexable,
                    title_score=score,
                    author_match=authors,
                    year_delta=delta,
                    checked_sources=["dossier"],
                    notes=[f"dossier:{data.get('key', '')}", *notes],
                )
    if reserved:
        return ReferenceVerdict(
            ref,
            RefStatus.DOSSIER_MISCITED,
            indexable,
            checked_sources=["dossier"],
            notes=["unknown_dossier_doi"],
        )
    return None


def verify_reference(
    ref: ParsedReference,
    dossier_pubs: Sequence[Mapping[str, Any] | OwnPublication],
    client: EvidenceClient,
    cfg: MatchConfig | None = None,
) -> ReferenceVerdict:
    cfg = cfg or MatchConfig()
    indexable = ref.kind_guess == "journal_article" and bool(
        ref.year and ref.year >= cfg.indexable_since
    )
    if result := _dossier(ref, dossier_pubs, cfg, indexable):
        return result
    checked = ["dossier"]
    notes: list[str] = []
    records: list[tuple[WorkRecord, bool]] = []
    unresolved = False
    wrong_doi: WorkRecord | None = None

    def fetch(source: str, call: Callable[[], Any]) -> Any:
        if source not in checked:
            checked.append(source)
        try:
            return call()
        except (
            httpx.HTTPError,
            OfflineCacheMiss,
            ValueError,
            KeyError,
            TypeError,
            ParseError,
        ) as exc:
            notes.append(f"{source}_unavailable:{type(exc).__name__}")
            return None

    def assess() -> ReferenceVerdict | None:
        options = []
        for work, identifier in records:
            score = title_similarity(ref.title, work.title)
            if not ref.title and identifier:
                score = 100.0
            raw_title = score < cfg.title_ok and (
                raw_mentions_title(ref.raw, work.title, cfg)
                or main_title_match(ref.title, work.title)
            )
            if raw_title:
                # The parse split the reference wrongly; the raw text names this work.
                score = cfg.title_ok
            authors = author_overlap(ref.authors, work.authors)
            if authors in {"none", "unknown"} and raw_mentions_authors(ref.raw, work.authors):
                authors = "some"
            # A reference that names no authors cannot name the wrong ones.
            authorless = authors == "none" and authors_are_title(ref.authors, work.title, cfg)
            if authorless:
                authors = "unknown"
            delta = ref.year - work.year if ref.year and work.year else None
            if score < cfg.title_ok:
                continue
            extra = []
            if authors == "none" and min(len(ref.authors), len(work.authors)) >= (
                cfg.misattributed_min_authors
            ):
                specific = len((ref.title or "").split()) >= cfg.misattributed_min_title_words
                if not (identifier or specific):
                    continue
                status = RefStatus.MISATTRIBUTED
                extra.append("authors_mismatch")
            elif authors in {"first", "some"} or (
                authors == "unknown" and (not ref.authors or authorless)
            ):
                if delta is not None and abs(delta) > cfg.year_tolerance:
                    extra.append("year_mismatch")
                if venue_disagrees(ref.venue, work.venue, cfg):
                    extra.append("venue_mismatch")
                if unresolved:
                    extra.append("doi_unresolved")
                elif ref.doi and work.doi and ref.doi != normalize_doi(work.doi):
                    extra.append("doi_mismatch")
                status = RefStatus.VERIFIED_WITH_ERRORS if extra else RefStatus.VERIFIED
                if raw_title:
                    extra.append("matched_on_raw_text")
                if delta is None:
                    extra.append("year_unknown")
                if not ref.title:
                    extra.append("identifier_only")
                if authorless:
                    extra.append("authors_absent")
            else:
                continue
            verdict = ReferenceVerdict(
                ref, status, indexable, work, score, authors, delta, list(checked), [*notes, *extra]
            )
            rank = {
                RefStatus.VERIFIED: 3,
                RefStatus.VERIFIED_WITH_ERRORS: 2,
                RefStatus.MISATTRIBUTED: 1,
            }[status]
            options.append((rank, score, verdict))
        if wrong_doi is not None:
            # The DOI leads a reader to a different work. Record whether the cited title and
            # authors nevertheless match a real work, so scoring can tell a wrong identifier on a
            # real paper from a fabricated attribution.
            elsewhere = any(
                o[2].status == RefStatus.VERIFIED and o[2].best is not wrong_doi for o in options
            )
            return ReferenceVerdict(
                ref,
                RefStatus.MISATTRIBUTED,
                indexable,
                wrong_doi,
                title_similarity(ref.title, wrong_doi.title),
                author_overlap(ref.authors, wrong_doi.authors),
                ref.year - wrong_doi.year if ref.year and wrong_doi.year else None,
                list(checked),
                [
                    *notes,
                    "doi_points_to_different_work",
                    *(["title_verified_elsewhere"] if elsewhere else []),
                ],
            )
        return max(options, key=lambda x: (x[0], x[1]))[2] if options else None

    if not any((ref.title, ref.doi, ref.arxiv_id, ref.url)):
        return ReferenceVerdict(ref, RefStatus.UNPARSEABLE, indexable, checked_sources=checked)
    if ref.doi:
        resolved = fetch("doi", lambda: doi.resolve_doi(ref.doi, client))
        if resolved == doi.DoiStatus.UNRESOLVED:
            cr = fetch("crossref", lambda: crossref.by_doi(ref.doi, client))
            oa = fetch("openalex", lambda: openalex.by_doi(ref.doi, client))
            corroborated = [r for r in (cr or []) + (oa or []) if normalize_doi(r.doi) == ref.doi]
            # doi.org's 404 needs a second registry's 404. Crossref alone suffices when OpenAlex
            # was skipped for the run (no key or spent quota), so detection does not depend on it.
            openalex_skipped = any(n == "openalex_unavailable:SourceExhausted" for n in notes)
            unresolved = (
                cr is not None and (oa is not None or openalex_skipped) and not corroborated
            )
            resolved = corroborated
            if not unresolved and not corroborated:
                notes.append("doi_404_not_corroborated")
        for work in resolved or []:
            records.append((work, True))
            if (
                ref.title
                and work.title
                and title_similarity(ref.title, work.title) < cfg.doi_unrelated
                and not raw_mentions_title(ref.raw, work.title, cfg)
                and not main_title_match(ref.title, work.title)
            ):
                wrong_doi = work
        if (result := assess()) and result.status == RefStatus.VERIFIED:
            return result
    if ref.arxiv_id:
        records.extend(
            (work, True)
            for work in (fetch("arxiv", lambda: arxiv.resolve_arxiv(ref.arxiv_id, client)) or [])
        )
        if (result := assess()) and result.status == RefStatus.VERIFIED:
            return result
    if ref.title:
        searches = [
            (
                "crossref",
                lambda: crossref.search(
                    ref.title, client, ref.authors[0] if ref.authors else None, ref.year
                ),
            ),
            ("semanticscholar", lambda: semanticscholar.search(ref.title, client)),
            # Last: a key gives about 1,000 searches a day, so spend them only on references
            # Crossref and Semantic Scholar could not verify.
            ("openalex", lambda: openalex.search(ref.title, client)),
        ]
        for source, call in searches:
            records.extend((work, False) for work in (fetch(source, call) or []))
            if (result := assess()) and result.status == RefStatus.VERIFIED:
                return result
    if ref.url:
        records.extend(
            (work, False) for work in (fetch("url", lambda: url.resolve_url(ref.url, client)) or [])
        )
        if (result := assess()) and result.status == RefStatus.VERIFIED:
            return result
    if ref.title:
        records.extend(
            (work, False) for work in (fetch("exa", lambda: exa.search(ref.title, client)) or [])
        )
    if result := assess():
        return result
    best = max(
        (work for work, _ in records),
        key=lambda work: title_similarity(ref.title, work.title),
        default=None,
    )
    return ReferenceVerdict(
        ref,
        RefStatus.DOI_UNRESOLVED if unresolved else RefStatus.NOT_FOUND,
        indexable,
        best,
        title_similarity(ref.title, best.title) if best else 0.0,
        author_overlap(ref.authors, best.authors) if best else "unknown",
        ref.year - best.year if best and ref.year and best.year else None,
        checked,
        [*notes, *(["doi_unresolved"] if unresolved else []), "could_not_verify"],
    )


def verify_references(
    refs: Sequence[ParsedReference],
    dossier_pubs: Sequence[Mapping[str, Any] | OwnPublication],
    client: EvidenceClient,
    cfg: MatchConfig | None = None,
    workers: int = 8,
) -> list[ReferenceVerdict]:
    """Verify in parallel; the client's per-host rate limits still apply. Order is preserved."""
    if workers <= 1 or len(refs) <= 1:
        return [verify_reference(ref, dossier_pubs, client, cfg) for ref in refs]
    with ThreadPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(lambda r: verify_reference(r, dossier_pubs, client, cfg), refs))


def summarize(verdicts: Sequence[ReferenceVerdict]) -> dict:
    def counts(items: Sequence[ReferenceVerdict]) -> dict[str, int]:
        counted = Counter(v.status for v in items)
        return {status.value: counted[status] for status in RefStatus}

    return {
        "total": len(verdicts),
        "counts": counts(verdicts),
        "by_indexable": {
            "true": counts([v for v in verdicts if v.indexable]),
            "false": counts([v for v in verdicts if not v.indexable]),
        },
    }
