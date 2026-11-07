from __future__ import annotations

from xml.etree import ElementTree

from proposalbench.evidence.http import EvidenceClient
from proposalbench.evidence.records import WorkRecord, family_name
from proposalbench.parse.references import normalize_doi

NS = {"a": "http://www.w3.org/2005/Atom", "x": "http://arxiv.org/schemas/atom"}


def resolve_arxiv(arxiv_id: str, client: EvidenceClient) -> list[WorkRecord]:
    response = client.request(
        "GET", "https://export.arxiv.org/api/query", source="arxiv", params={"id_list": arxiv_id}
    )
    response.raise_for_status()
    records = []
    for entry in ElementTree.fromstring(response.content).findall("a:entry", NS):
        url = entry.findtext("a:id", "", NS)
        if "/abs/" not in url:
            continue
        date = entry.findtext("a:published", "", NS)
        records.append(
            WorkRecord(
                "arxiv",
                url.split("/abs/")[-1],
                normalize_doi(entry.findtext("x:doi", None, NS)),
                " ".join(entry.findtext("a:title", "", NS).split()),
                [family_name(a.findtext("a:name", "", NS)) for a in entry.findall("a:author", NS)],
                int(date[:4]) if date else None,
                entry.findtext("x:journal_ref", None, NS),
                "preprint",
                url,
                " ".join(entry.findtext("a:summary", "", NS).split()) or None,
                {"id": url, "published": date},
            )
        )
    return records
