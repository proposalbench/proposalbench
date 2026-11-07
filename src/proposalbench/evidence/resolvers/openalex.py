from __future__ import annotations

from urllib.parse import quote

from proposalbench.evidence.http import EvidenceClient
from proposalbench.evidence.records import WorkRecord, family_name
from proposalbench.parse.references import normalize_doi

BASE = "https://api.openalex.org/works"


def reconstruct_abstract(index: dict[str, list[int]] | None) -> str | None:
    if not index:
        return None
    return " ".join(
        word
        for _, word in sorted((pos, word) for word, positions in index.items() for pos in positions)
    )


def _record(data: dict) -> WorkRecord:
    location = data.get("primary_location") or {}
    venue = location.get("source") or {}
    return WorkRecord(
        "openalex",
        data["id"],
        normalize_doi(data.get("doi")),
        data.get("title") or data.get("display_name"),
        [
            family_name(a["author"]["display_name"])
            for a in data.get("authorships", [])
            if a.get("author", {}).get("display_name")
        ],
        data.get("publication_year"),
        venue.get("display_name"),
        "journal_article" if data.get("type") == "article" else data.get("type", "other"),
        location.get("landing_page_url") or data.get("doi"),
        reconstruct_abstract(data.get("abstract_inverted_index")),
        {k: data[k] for k in ("id", "doi", "title", "publication_year") if k in data},
    )


def search(title: str, client: EvidenceClient) -> list[WorkRecord]:
    response = client.request(
        "GET", BASE, source="openalex", params={"search": title, "per-page": 5}
    )
    response.raise_for_status()
    return [_record(item) for item in response.json()["results"]]


def by_doi(doi: str, client: EvidenceClient) -> list[WorkRecord]:
    response = client.request(
        "GET", f"{BASE}/https://doi.org/{quote(doi, safe='/')}", source="openalex"
    )
    if response.status_code == 404:
        return []
    response.raise_for_status()
    return [_record(response.json())]
