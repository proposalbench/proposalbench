from __future__ import annotations

import httpx
import pytest

from proposalbench.evidence.resolvers import (
    arxiv,
    crossref,
    doi,
    exa,
    openalex,
    semanticscholar,
    url,
)


@pytest.mark.parametrize(
    "value,name,source",
    [
        ("10.5281/zenodo.3727209", "zenodo_doi", "datacite"),
        ("10.1126/sciadv.adt3813", "kobak_doi", "crossref"),
    ],
)
def test_doi_records(fixture_client, value, name, source):
    client = fixture_client({f"https://doi.org/{value}": name})
    (record,) = doi.resolve_doi(value, client)
    assert record.source == source and record.doi == value
    assert record.title and record.authors and record.year
    assert client.calls[0]["headers"]["Accept"] == "application/vnd.citationstyles.csl+json"


def test_doi_404_and_network_failure(fixture_client):
    target = "https://doi.org/10.5555/proposalbench.nonexistent.2030"
    client = fixture_client({target: "missing_doi"})
    assert (
        doi.resolve_doi("10.5555/proposalbench.nonexistent.2030", client)
        == doi.DoiStatus.UNRESOLVED
    )
    with pytest.raises(httpx.ConnectError):
        doi.resolve_doi("10.1234/failure", client)


def test_crossref_article_and_book(fixture_client):
    client = fixture_client(
        {
            crossref.BASE: "kobak_crossref",
            f"{crossref.BASE}/10.1007/978-0-387-84858-7": "elements_book",
        }
    )
    records = crossref.search("Delving into LLM-assisted writing", client, "Kobak", 2025)
    assert records[0].doi == "10.1126/sciadv.adt3813"
    assert records[0].year == 2025
    assert records[0].venue == "Science Advances"
    (book,) = crossref.by_doi("10.1007/978-0-387-84858-7", client)
    assert book.kind == "book"
    assert "Statistical Learning" in book.title


def test_arxiv_and_openalex(fixture_client):
    client = fixture_client(
        {
            "https://export.arxiv.org/api/query": "attention_arxiv",
            f"{openalex.BASE}/https://doi.org/10.48550/arxiv.1706.03762": "attention_openalex",
        }
    )
    (paper,) = arxiv.resolve_arxiv("1706.03762", client)
    assert paper.title == "Attention Is All You Need"
    assert paper.authors[0] == "Vaswani" and paper.year == 2017
    assert paper.abstract and paper.kind == "preprint"
    (work,) = openalex.by_doi("10.48550/arxiv.1706.03762", client)
    assert work.authors[0] == "Vaswani" and work.year == 2025
    assert work.doi == "10.65215/2q58a426"
    assert work.abstract.startswith("The dominant")
    assert openalex.reconstruct_abstract({"world": [1, 3], "Hello": [0, 2]}) == (
        "Hello world Hello world"
    )
    assert openalex.reconstruct_abstract(None) is None


def test_grey_literature_and_url_status(fixture_client):
    target = "https://www.who.int/publications/i/item/9789240083851"
    client = fixture_client(
        {
            "https://api.exa.ai/search": "who_exa",
            target: "who_report",
            "https://example.org/missing": (404, {}),
        }
    )
    records = exa.search("WHO Global tuberculosis report 2023", client)
    assert records[0].title == "Global tuberculosis report 2023"
    (record,) = url.resolve_url(target, client)
    assert record.raw_ref["status"] == 200
    assert "tuberculosis" in record.title.lower()
    (missing,) = url.resolve_url("https://example.org/missing", client)
    assert missing.raw_ref["status"] == 404 and missing.title is None


def test_semantic_synthetic_success_and_live_denial(fixture_client):
    data = {
        "paperId": "test",
        "title": "Attention is all you need",
        "authors": [{"name": "Ashish Vaswani"}],
        "year": 2017,
        "venue": "NeurIPS",
        "externalIds": {"DOI": "10.48550/arXiv.1706.03762"},
        "abstract": "Example abstract.",
    }
    target = f"{semanticscholar.BASE}/search/match"
    client = fixture_client({target: (200, {"data": [data]})})
    (record,) = semanticscholar.search(data["title"], client)
    assert record.authors == ["Vaswani"] and record.abstract == "Example abstract."
    denied = fixture_client({target: "attention_semanticscholar"})
    with pytest.raises(httpx.HTTPStatusError):
        semanticscholar.search(data["title"], denied)


def test_empty_and_malformed_payloads(fixture_client):
    client = fixture_client(
        {
            crossref.BASE: (200, {"message": {"items": []}}),
            openalex.BASE: (200, {"results": []}),
            f"{semanticscholar.BASE}/search/match": (404, {}),
        }
    )
    assert crossref.search("Invented title", client) == []
    assert openalex.search("Invented title", client) == []
    assert semanticscholar.search("Invented title", client) == []


def test_downstream_404_is_not_an_unregistered_doi():
    from proposalbench.evidence.cache import EvidenceCache
    from proposalbench.evidence.http import EvidenceClient

    def serve(request):
        if request.url.host == "doi.org":
            return httpx.Response(302, headers={"location": "https://publisher.example/missing"})
        return httpx.Response(404)

    with (
        EvidenceCache(":memory:") as cache,
        EvidenceClient(cache, transport=httpx.MockTransport(serve)) as client,
    ):
        with pytest.raises(httpx.HTTPStatusError):
            doi.resolve_doi("10.1234/registered", client)
        with pytest.raises(httpx.HTTPStatusError):
            doi.resolve_doi("10.1234/registered", client)
