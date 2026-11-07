from __future__ import annotations

from urllib.parse import quote

from proposalbench.evidence.http import EvidenceClient
from proposalbench.evidence.records import WorkRecord, from_csl

BASE = "https://api.crossref.org/works"


def search(
    title: str, client: EvidenceClient, author: str | None = None, year: int | None = None
) -> list[WorkRecord]:
    query = " ".join(str(x) for x in (title, author, year) if x)
    response = client.request(
        "GET", BASE, source="crossref", params={"query.bibliographic": query, "rows": 5}
    )
    response.raise_for_status()
    return [from_csl(item) for item in response.json()["message"]["items"]]


def by_doi(doi: str, client: EvidenceClient) -> list[WorkRecord]:
    response = client.request("GET", f"{BASE}/{quote(doi, safe='/')}", source="crossref")
    if response.status_code == 404:
        return []
    response.raise_for_status()
    return [from_csl(response.json()["message"])]
