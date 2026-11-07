from __future__ import annotations

from proposalbench.evidence.http import EvidenceClient
from proposalbench.evidence.records import WorkRecord


def search(query: str, client: EvidenceClient) -> list[WorkRecord]:
    response = client.request(
        "POST", "https://api.exa.ai/search", source="exa", json={"query": query, "numResults": 5}
    )
    response.raise_for_status()
    records = []
    for item in response.json().get("results", []):
        date = item.get("publishedDate") or ""
        records.append(
            WorkRecord(
                "exa",
                item.get("id") or item["url"],
                title=item.get("title"),
                year=int(date[:4]) if date[:4].isdigit() else None,
                kind="web",
                url=item["url"],
                raw_ref={k: item[k] for k in ("id", "url", "title", "publishedDate") if k in item},
            )
        )
    return records
