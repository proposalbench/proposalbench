from __future__ import annotations

import httpx

from proposalbench.evidence.http import EvidenceClient, OfflineCacheMiss
from proposalbench.evidence.records import WorkRecord
from proposalbench.evidence.resolvers import openalex, semanticscholar
from proposalbench.evidence.verify import ReferenceVerdict, RefStatus


def get_abstract(verdict: ReferenceVerdict, client: EvidenceClient) -> tuple[str | None, str]:
    # A search candidate or a misattributed DOI is not evidence for the cited claim.
    if (
        verdict.status not in {RefStatus.VERIFIED, RefStatus.VERIFIED_WITH_ERRORS}
        or not verdict.best
    ):
        return None, "none"
    return get_work_abstract(verdict.best, client)


def get_work_abstract(work: WorkRecord, client: EvidenceClient) -> tuple[str | None, str]:
    """Get an abstract for an identified work, including retrieval candidates."""
    if work.abstract:
        return work.abstract, work.source
    if work.doi:
        for resolver in (openalex, semanticscholar):
            try:
                records = resolver.by_doi(work.doi, client)
            except (httpx.HTTPError, OfflineCacheMiss, ValueError, KeyError, TypeError):
                continue
            for record in records:
                if record.doi == work.doi and record.abstract:
                    return record.abstract, record.source
    return None, "none"
