"""Manual fixture capture: uv run python tests/evidence/record_fixtures.py.

Existing captures are preserved. Only public response payloads and sanitized request
metadata are written; credentials are loaded by EvidenceClient.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from proposalbench.evidence.cache import EvidenceCache, safe_url
from proposalbench.evidence.http import EvidenceClient

ROOT = Path(__file__).parents[1] / "fixtures" / "evidence"
REQUESTS = [
    (
        "kobak_crossref",
        "GET",
        "https://api.crossref.org/works",
        "crossref",
        {
            "query.bibliographic": (
                "Delving into LLM-assisted writing in biomedical publications "
                "through excess vocabulary"
            ),
            "rows": 5,
        },
        None,
    ),
    (
        "attention_arxiv",
        "GET",
        "https://export.arxiv.org/api/query",
        "arxiv",
        {"id_list": "1706.03762"},
        None,
    ),
    ("zenodo_doi", "GET", "https://doi.org/10.5281/zenodo.3727209", "doi", {}, None),
    (
        "book_crossref",
        "GET",
        "https://api.crossref.org/works/10.1017/CBO9780511805064",
        "crossref",
        {},
        None,
    ),
    ("who_url", "GET", "https://www.who.int/publications/i/item/9789240080873", "url", {}, None),
    (
        "missing_doi",
        "GET",
        "https://doi.org/10.5555/proposalbench.nonexistent.2030",
        "doi",
        {},
        None,
    ),
    (
        "attention_openalex",
        "GET",
        "https://api.openalex.org/works/https://doi.org/10.48550/arXiv.1706.03762",
        "openalex",
        {},
        None,
    ),
    (
        "attention_semanticscholar",
        "GET",
        "https://api.semanticscholar.org/graph/v1/paper/search/match",
        "semanticscholar",
        {
            "query": "Attention is all you need",
            "fields": "title,authors,year,venue,externalIds,abstract",
        },
        None,
    ),
    (
        "who_exa",
        "POST",
        "https://api.exa.ai/search",
        "exa",
        {},
        {"query": "WHO Global tuberculosis report 2023", "numResults": 5},
    ),
]
REQUESTS += [
    ("kobak_doi", "GET", "https://doi.org/10.1126/sciadv.adt3813", "doi", {}, None),
    (
        "elements_book",
        "GET",
        "https://api.crossref.org/works/10.1007/978-0-387-84858-7",
        "crossref",
        {},
        None,
    ),
    ("who_report", "GET", "https://www.who.int/publications/i/item/9789240083851", "url", {}, None),
    (
        "missing_crossref",
        "GET",
        "https://api.crossref.org/works/10.5555/proposalbench.nonexistent.2030",
        "crossref",
        {},
        None,
    ),
    (
        "missing_openalex",
        "GET",
        "https://api.openalex.org/works/https://doi.org/10.5555/proposalbench.nonexistent.2030",
        "openalex",
        {},
        None,
    ),
    (
        "fabricated_crossref",
        "GET",
        "https://api.crossref.org/works",
        "crossref",
        {
            "query.bibliographic": "Quantum marmalade networks for lunar tuberculosis Smith 2024",
            "rows": 5,
        },
        None,
    ),
    (
        "fabricated_openalex",
        "GET",
        "https://api.openalex.org/works",
        "openalex",
        {"search": "Quantum marmalade networks for lunar tuberculosis", "per-page": 5},
        None,
    ),
]


def main() -> None:
    manifest_path = ROOT / "manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    with EvidenceCache(":memory:") as cache, EvidenceClient(cache, retries=0) as client:
        for name, method, url, source, params, body in REQUESTS:
            if name in manifest and manifest[name].get("file"):
                continue
            try:
                response = client.request(
                    method,
                    url,
                    source=source,
                    params=params,
                    json=body,
                    headers={"Accept": "application/vnd.citationstyles.csl+json"}
                    if source == "doi"
                    else None,
                )
                content_type = response.headers.get("content-type", "")
                suffix = (
                    "json" if "json" in content_type else "xml" if "xml" in content_type else "html"
                )
                filename = f"{name}.{suffix}"
                (ROOT / filename).write_bytes(response.content)
                manifest[name] = {
                    "file": filename,
                    "url": safe_url(url),
                    "params": params,
                    "method": method,
                    "body": body,
                    "status": response.status_code,
                    "content_type": content_type,
                    "response_url": safe_url(str(response.url)),
                    "fetched_at": datetime.now(UTC).isoformat(),
                }
                print(name, response.status_code, content_type)
            except Exception as exc:
                manifest[name] = {"url": safe_url(url), "error": type(exc).__name__}
                print(name, type(exc).__name__)
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
