from __future__ import annotations

from urllib.parse import quote

from proposalbench.evidence.http import EvidenceClient
from proposalbench.evidence.records import WorkRecord, family_name
from proposalbench.parse.references import normalize_doi

BASE = "https://api.semanticscholar.org/graph/v1/paper"
FIELDS = "title,authors,year,venue,externalIds,abstract"


def _record(data: dict) -> WorkRecord:
    return WorkRecord(
        "semanticscholar",
        data.get("paperId", ""),
        normalize_doi((data.get("externalIds") or {}).get("DOI")),
        data.get("title"),
        [family_name(a["name"]) for a in data.get("authors", []) if a.get("name")],
        data.get("year"),
        data.get("venue") or None,
        "other",
        data.get("url"),
        data.get("abstract"),
        {k: data[k] for k in ("paperId", "title", "externalIds", "year") if k in data},
    )


def search(title: str, client: EvidenceClient) -> list[WorkRecord]:
    response = client.request(
        "GET",
        f"{BASE}/search/match",
        source="semanticscholar",
        params={"query": title, "fields": FIELDS},
    )
    if response.status_code == 404:
        return []
    response.raise_for_status()
    return [_record(item) for item in response.json().get("data", [])]


def by_doi(doi: str, client: EvidenceClient) -> list[WorkRecord]:
    response = client.request(
        "GET",
        f"{BASE}/DOI:{quote(doi, safe='/')}",
        source="semanticscholar",
        params={"fields": FIELDS},
    )
    if response.status_code == 404:
        return []
    response.raise_for_status()
    return [_record(response.json())]
