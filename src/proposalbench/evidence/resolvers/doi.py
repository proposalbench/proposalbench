from __future__ import annotations

from enum import StrEnum
from urllib.parse import quote, urlsplit

from proposalbench.evidence.http import EvidenceClient
from proposalbench.evidence.records import WorkRecord, from_csl
from proposalbench.parse.references import normalize_doi


class DoiStatus(StrEnum):
    UNRESOLVED = "unresolved"


def resolve_doi(doi: str, client: EvidenceClient) -> list[WorkRecord] | DoiStatus:
    doi = normalize_doi(doi) or doi
    response = client.request(
        "GET",
        f"https://doi.org/{quote(doi, safe='/')}",
        source="doi",
        headers={"Accept": "application/vnd.citationstyles.csl+json"},
    )
    if response.status_code == 404 and response.url.host == "doi.org":
        return DoiStatus.UNRESOLVED
    response.raise_for_status()
    data = response.json()
    agency = str(data.get("agency", "")).casefold()
    datacite = "datacite" in agency or "datacite" in str(data.get("source", "")).casefold()
    host = urlsplit(str(response.url)).hostname or ""
    datacite = datacite or "datacite.org" in host or "crosscite.org" in host
    datacite = datacite or data.get("publisher", "").casefold() == "zenodo"
    return [from_csl(data, "datacite" if datacite else "crossref")]
