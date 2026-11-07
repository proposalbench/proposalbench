from __future__ import annotations

from dataclasses import replace

import httpx
import pytest

from proposalbench.evidence.abstracts import get_abstract
from proposalbench.evidence.match import (
    MatchConfig,
    author_overlap,
    normalize_title,
    title_similarity,
)
from proposalbench.evidence.records import WorkRecord
from proposalbench.evidence.resolvers import crossref, openalex, semanticscholar
from proposalbench.evidence.verify import (
    ReferenceVerdict,
    RefStatus,
    summarize,
    verify_reference,
    verify_references,
)
from proposalbench.parse.references import ParsedReference, parse_references
from proposalbench.tasks.schema import OwnPublication

TITLE = "Delving into LLM-assisted writing in biomedical publications through excess vocabulary"
MISSING = "10.5555/proposalbench.nonexistent.2030"


def reference(**kwargs):
    return replace(
        ParsedReference(
            0,
            None,
            TITLE,
            title=TITLE,
            authors=["Kobak"],
            year=2025,
            venue="Science Advances",
            kind_guess="journal_article",
        ),
        **kwargs,
    )


def missing_routes():
    return {
        f"https://doi.org/{MISSING}": "missing_doi",
        f"{crossref.BASE}/{MISSING}": "missing_crossref",
        f"{openalex.BASE}/https://doi.org/{MISSING}": "missing_openalex",
    }


@pytest.mark.parametrize("as_model", [False, True])
def test_dossier_and_reserved_namespace(fixture_client, as_model):
    data = {
        "key": "own-1",
        "title": "A fictional applicant publication",
        "authors": ["Jane Smith"],
        "year": 2022,
        "venue": "Nature",
        "doi": "10.99999/pb.own-1",
    }
    pub = OwnPublication(**data) if as_model else data
    ref = reference(title=data["title"], authors=["Smith"], year=2022, venue="Nature")
    client = fixture_client({})
    assert verify_reference(ref, [pub], client).status == RefStatus.DOSSIER
    assert (
        verify_reference(replace(ref, doi=data["doi"]), [pub], client).status == RefStatus.DOSSIER
    )
    for changed in [
        replace(ref, year=2020),
        replace(ref, authors=["Jones", "Brown"]),
        replace(ref, venue="Lancet"),
        replace(ref, doi="10.99999/pb.unknown"),
    ]:
        assert verify_reference(changed, [pub], client).status == RefStatus.DOSSIER_MISCITED
    assert not client.calls


def test_dossier_near_title_requires_evidenced_disagreement(fixture_client):
    pub = {
        "key": "own",
        "title": "Neural networks for clinical discovery",
        "authors": ["Smith"],
        "year": 2022,
        "venue": "Nature",
    }
    ref = reference(
        title="Neural networks in clinical discovery", authors=["Smith"], year=2020, venue="Nature"
    )
    cfg = MatchConfig(dossier_ok=99)
    assert 75 <= title_similarity(ref.title, pub["title"]) < cfg.dossier_ok
    assert (
        verify_reference(ref, [pub], fixture_client({}), cfg).status == RefStatus.DOSSIER_MISCITED
    )
    assert verify_reference(replace(ref, year=2022), [pub], fixture_client({}), cfg).status == (
        RefStatus.NOT_FOUND
    )


def test_verified_doi_and_early_exit(fixture_client):
    client = fixture_client({"https://doi.org/10.1126/sciadv.adt3813": "kobak_doi"})
    verdict = verify_reference(reference(doi="10.1126/sciadv.adt3813"), [], client)
    assert verdict.status == RefStatus.VERIFIED and verdict.indexable
    assert verdict.author_match in {"first", "some"}
    assert verdict.checked_sources == ["dossier", "doi"]
    assert len(client.calls) == 1


@pytest.mark.parametrize(
    "change,note", [({"year": 2020}, "year_mismatch"), ({"venue": "Lancet"}, "venue_mismatch")]
)
def test_evidenced_metadata_errors(fixture_client, change, note):
    verdict = verify_reference(
        reference(**change), [], fixture_client({crossref.BASE: "kobak_crossref"})
    )
    assert verdict.status == RefStatus.VERIFIED_WITH_ERRORS
    assert note in verdict.notes


def test_author_misattribution_and_single_author_caution(fixture_client):
    client = fixture_client({crossref.BASE: "kobak_crossref"})
    verdict = verify_reference(reference(authors=["Smith", "Jones"]), [], client)
    assert verdict.status == RefStatus.MISATTRIBUTED
    assert "authors_mismatch" in verdict.notes
    verdict = verify_reference(reference(authors=["Smith"]), [], client)
    assert verdict.status == RefStatus.NOT_FOUND


def test_wrong_doi_overrides_title_verification(fixture_client):
    client = fixture_client(
        {"https://doi.org/10.5281/zenodo.3727209": "zenodo_doi", crossref.BASE: "kobak_crossref"}
    )
    verdict = verify_reference(reference(doi="10.5281/zenodo.3727209"), [], client)
    assert verdict.status == RefStatus.MISATTRIBUTED
    assert verdict.best.source == "datacite"
    assert "doi_points_to_different_work" in verdict.notes


def test_unresolved_and_title_recovery(fixture_client):
    ref = reference(doi=MISSING)
    client = fixture_client(missing_routes())
    verdict = verify_reference(ref, [], client)
    assert verdict.status == RefStatus.DOI_UNRESOLVED
    assert {"doi", "crossref", "openalex", "semanticscholar", "exa"} <= set(verdict.checked_sources)
    client = fixture_client({**missing_routes(), crossref.BASE: "kobak_crossref"})
    verdict = verify_reference(ref, [], client)
    assert verdict.status == RefStatus.VERIFIED_WITH_ERRORS
    assert "doi_unresolved" in verdict.notes


def test_404_without_corroboration_is_not_unresolved(fixture_client):
    routes = missing_routes()
    del routes[f"{openalex.BASE}/https://doi.org/{MISSING}"]
    verdict = verify_reference(reference(doi=MISSING), [], fixture_client(routes))
    assert verdict.status == RefStatus.NOT_FOUND
    assert "doi_404_not_corroborated" in verdict.notes


def test_doi_404_with_indexed_record(fixture_client):
    value = "10.1126/sciadv.adt3813"
    client = fixture_client(
        {
            f"https://doi.org/{value}": (404, {}),
            f"{crossref.BASE}/{value}": (
                200,
                {
                    "message": {
                        "DOI": value,
                        "title": [TITLE],
                        "author": [{"family": "Kobak"}],
                        "published": {"date-parts": [[2025]]},
                    }
                },
            ),
            f"{openalex.BASE}/https://doi.org/{value}": (404, {}),
        }
    )
    verdict = verify_reference(reference(doi=value), [], client)
    assert verdict.status == RefStatus.VERIFIED


def test_invented_work_is_not_found_never_fabricated(fixture_client):
    ref = reference(
        title="Quantum marmalade networks for lunar tuberculosis",
        authors=["Smith", "Jones"],
        year=2024,
    )
    client = fixture_client(
        {crossref.BASE: "fabricated_crossref", openalex.BASE: "fabricated_openalex"}
    )
    verdict = verify_reference(ref, [], client)
    assert verdict.status == RefStatus.NOT_FOUND
    assert "could_not_verify" in verdict.notes
    assert all("fabricat" not in status.value for status in RefStatus)


def test_unparseable_and_indexability(fixture_client):
    refs = [ParsedReference(0, None, "???"), reference(year=1999), reference(kind_guess="book")]
    verdicts = verify_references(refs, [], fixture_client({}))
    assert verdicts[0].status == RefStatus.UNPARSEABLE
    assert not any(v.indexable for v in verdicts)
    summary = summarize(verdicts)
    assert summary["counts"]["unparseable"] == 1 and summary["total"] == 3
    assert summary["by_indexable"]["false"]["not_found"] == 2
    assert set(summary["counts"]) == {s.value for s in RefStatus}


def test_arxiv_identifier_and_title_only_reference(fixture_client):
    (ref,) = parse_references(
        "Vaswani, A. et al. (2017). Attention is all you need. arXiv:1706.03762."
    )
    client = fixture_client({"https://export.arxiv.org/api/query": "attention_arxiv"})
    verdict = verify_reference(ref, [], client)
    assert verdict.status == RefStatus.VERIFIED
    assert not verdict.indexable
    assert get_abstract(verdict, client)[1] == "arxiv"
    client = fixture_client({crossref.BASE: "kobak_crossref"})
    assert verify_reference(reference(authors=[]), [], client).status == RefStatus.VERIFIED


def test_missing_source_authors_does_not_establish_identity(fixture_client):
    client = fixture_client(
        {
            "https://api.exa.ai/search": (
                200,
                {"results": [{"id": "1", "url": "https://example.org", "title": TITLE}]},
            )
        }
    )
    assert verify_reference(reference(), [], client).status == RefStatus.NOT_FOUND


def test_missing_doi_metadata_does_not_establish_doi_absence(fixture_client):
    routes = missing_routes()
    routes[f"{openalex.BASE}/https://doi.org/{MISSING}"] = (503, {})
    verdict = verify_reference(reference(doi=MISSING), [], fixture_client(routes))
    assert verdict.status == RefStatus.NOT_FOUND


def test_network_and_malformed_failures_are_not_errors(fixture_client):
    client = fixture_client(
        {crossref.BASE: httpx.ReadTimeout("offline"), openalex.BASE: (200, {"unexpected": "shape"})}
    )
    verdict = verify_reference(reference(), [], client)
    assert verdict.status == RefStatus.NOT_FOUND
    assert "crossref_unavailable:ReadTimeout" in verdict.notes
    assert "openalex_unavailable:KeyError" in verdict.notes


def test_abstract_fallbacks_and_reject_unverified_candidate(fixture_client):
    doi = "10.1234/test"
    work = WorkRecord("crossref", doi, doi, TITLE)
    verdict = ReferenceVerdict(reference(), RefStatus.VERIFIED, True, work)
    oa = {
        "id": "W1",
        "doi": doi,
        "title": TITLE,
        "abstract_inverted_index": {"Useful": [0], "abstract.": [1]},
    }
    client = fixture_client({f"{openalex.BASE}/https://doi.org/{doi}": (200, oa)})
    assert get_abstract(verdict, client) == ("Useful abstract.", "openalex")
    client = fixture_client(
        {
            f"{semanticscholar.BASE}/DOI:{doi}": (
                200,
                {"paperId": "1", "externalIds": {"DOI": doi}, "abstract": "Fallback."},
            )
        }
    )
    assert get_abstract(verdict, client) == ("Fallback.", "semanticscholar")
    assert get_abstract(replace(verdict, status=RefStatus.NOT_FOUND), client) == (None, "none")
    assert get_abstract(verdict, fixture_client({})) == (None, "none")


def test_match_normalization_and_author_overlap():
    assert normalize_title("Étude—DE la MÉDECINE!") == "etude de la medecine"
    assert title_similarity("An important TITLE.", "an important title") == 100
    assert title_similarity("tiny", "tiny title with many extra words") < 60
    assert author_overlap(["García", "Smith"], ["Garcia", "Jones"]) == "first"
    assert author_overlap(["Smith", "Jones"], ["Brown", "Jones"]) == "some"
    assert author_overlap([], ["Smith"]) == "unknown"


def test_wrong_doi_without_resolution_is_evidenced_by_matched_metadata(fixture_client):
    verdict = verify_reference(
        reference(doi="10.1234/typo"), [], fixture_client({crossref.BASE: "kobak_crossref"})
    )
    assert verdict.status == RefStatus.VERIFIED_WITH_ERRORS
    assert "doi_mismatch" in verdict.notes


def test_openalex_and_semantic_search_cascade(fixture_client):
    ref = reference(title="Attention is all you need", authors=["Vaswani"], year=2017, venue=None)
    oa_record = {
        "id": "W1",
        "title": ref.title,
        "publication_year": 2017,
        "authorships": [{"author": {"display_name": "Ashish Vaswani"}}],
    }
    client = fixture_client({openalex.BASE: (200, {"results": [oa_record]})})
    verdict = verify_reference(ref, [], client)
    assert verdict.status == RefStatus.VERIFIED
    assert verdict.best.source == "openalex"
    ss_record = {
        "paperId": "1",
        "title": ref.title,
        "year": 2017,
        "authors": [{"name": "Ashish Vaswani"}],
    }
    client = fixture_client({f"{semanticscholar.BASE}/search/match": (200, {"data": [ss_record]})})
    verdict = verify_reference(ref, [], client)
    assert verdict.status == RefStatus.VERIFIED
    assert verdict.best.source == "semanticscholar"


def test_web_and_exa_cascade(fixture_client):
    target = "https://www.who.int/publications/i/item/9789240083851"
    ref = reference(
        title="Global tuberculosis report 2023",
        authors=[],
        year=2023,
        venue=None,
        kind_guess="report",
        url=target,
    )
    client = fixture_client({target: "who_report"})
    verdict = verify_reference(ref, [], client)
    assert verdict.status == RefStatus.VERIFIED
    assert verdict.best.source == "url"
    client = fixture_client({"https://api.exa.ai/search": "who_exa"})
    verdict = verify_reference(replace(ref, url=None), [], client)
    assert verdict.status == RefStatus.VERIFIED
    assert verdict.best.source == "exa"


def test_incomplete_dates_are_not_reported_as_errors(fixture_client):
    verdict = verify_reference(
        reference(year=None), [], fixture_client({crossref.BASE: "kobak_crossref"})
    )
    assert verdict.status == RefStatus.VERIFIED
    assert "year_unknown" in verdict.notes and verdict.year_delta is None


def test_identifier_only_and_reserved_unknown(fixture_client):
    ref = ParsedReference(0, None, "10.1126/sciadv.adt3813", doi="10.1126/sciadv.adt3813")
    client = fixture_client({"https://doi.org/10.1126/sciadv.adt3813": "kobak_doi"})
    verdict = verify_reference(ref, [], client)
    assert verdict.status == RefStatus.VERIFIED
    assert "identifier_only" in verdict.notes
    verdict = verify_reference(replace(ref, doi="10.99999/pb.unknown"), [], fixture_client({}))
    assert verdict.status == RefStatus.DOSSIER_MISCITED


def test_venue_abbreviations_are_not_evidenced_errors():
    from proposalbench.evidence.match import venue_disagrees

    assert not venue_disagrees("Sci. Adv.", "Science Advances", MatchConfig())
    assert not venue_disagrees(
        "PNAS", "Proceedings of the National Academy of Sciences", MatchConfig()
    )


def test_fabricated_reference_fixture_end_to_end(fixture_client):
    import json
    from pathlib import Path

    cases = json.loads(
        (
            Path(__file__).parents[1] / "fixtures" / "evidence" / "fabricated_references.json"
        ).read_text()
    )
    for case in cases:
        routes = missing_routes()
        routes["https://doi.org/10.5281/zenodo.3727209"] = "zenodo_doi"
        routes[crossref.BASE] = (
            "fabricated_crossref"
            if case["name"] in {"invented", "unresolved_doi"}
            else "kobak_crossref"
        )
        routes[openalex.BASE] = "fabricated_openalex"
        (ref,) = parse_references(case["raw"])
        verdict = verify_reference(ref, [], fixture_client(routes))
        assert verdict.status.value == case["expected"], case["name"]


def test_parse_errors_are_not_misattribution(fixture_client):
    # A mis-split reference: the parsed title and authors are fragments, but the raw text
    # names the work the DOI resolves to.
    raw = f"Kobak D. 2025. {TITLE}. Science Advances. 11. eadt3813. https://doi.org/10.1126/sciadv.adt3813"
    ref = reference(raw=raw, title="2025", authors=["D"], doi="10.1126/sciadv.adt3813")
    client = fixture_client({"https://doi.org/10.1126/sciadv.adt3813": "kobak_doi"})
    verdict = verify_reference(ref, [], client)
    assert verdict.status in {RefStatus.VERIFIED, RefStatus.VERIFIED_WITH_ERRORS}
    assert "doi_points_to_different_work" not in verdict.notes
    assert "matched_on_raw_text" in verdict.notes


def test_wrong_doi_still_detected_when_raw_text_names_another_work(fixture_client):
    client = fixture_client(
        {"https://doi.org/10.5281/zenodo.3727209": "zenodo_doi", crossref.BASE: "kobak_crossref"}
    )
    raw = f"Kobak D. et al. 2025. {TITLE}. Science Advances. https://doi.org/10.5281/zenodo.3727209"
    verdict = verify_reference(reference(raw=raw, doi="10.5281/zenodo.3727209"), [], client)
    assert verdict.status == RefStatus.MISATTRIBUTED
    assert "doi_points_to_different_work" in verdict.notes


def test_record_without_subtitle_is_the_cited_work():
    from proposalbench.evidence.match import main_title_match
    from proposalbench.evidence.records import from_csl

    assert main_title_match("DART: directed automated random testing", "DART")
    assert main_title_match("Seeing the State: Governance and Governmentality", "Seeing the State")
    assert not main_title_match("Seeing the State", "Seeing the State")
    assert not main_title_match("Data science in ecology", "Data")
    assert main_title_match("Garbage matters", "Garbage matters: Concepts in new geographies")
    record = from_csl({"title": ["Garbage Citizenship"], "subtitle": ["Vital Infrastructures"]})
    assert record.title == "Garbage Citizenship: Vital Infrastructures"


def test_any_doi_under_the_unregistered_registrant_is_fictional(fixture_client):
    ref = reference(doi="10.99999/data.safemother.2022", title="SafeMother dataset", authors=[])
    verdict = verify_reference(ref, [], fixture_client({}))
    assert verdict.status == RefStatus.DOSSIER_MISCITED
    assert verdict.checked_sources == ["dossier"]


def test_csl_record_with_null_date_parts():
    from proposalbench.evidence.records import from_csl

    record = from_csl(
        {
            "title": ["A title"],
            "issued": {"date-parts": [[None]]},
            "created": {"date-parts": [[2021, 3]]},
        }
    )
    assert record.year == 2021
    assert from_csl({"title": ["A title"], "issued": {"date-parts": [[None]]}}).year is None


def test_unresolved_doi_without_openalex(fixture_client):
    from proposalbench.evidence.http import SourceExhausted

    routes = missing_routes()
    routes[f"{openalex.BASE}/https://doi.org/{MISSING}"] = SourceExhausted("api.openalex.org")
    verdict = verify_reference(reference(doi=MISSING), [], fixture_client(routes))
    assert verdict.status == RefStatus.DOI_UNRESOLVED
    assert "doi_unresolved" in verdict.notes
    # A transient OpenAlex failure is not enough to call the DOI unresolved.
    routes[f"{openalex.BASE}/https://doi.org/{MISSING}"] = httpx.ConnectError("down")
    verdict = verify_reference(reference(doi=MISSING), [], fixture_client(routes))
    assert verdict.status != RefStatus.DOI_UNRESOLVED


def test_an_authorless_reference_is_not_misattribution(fixture_client):
    # "Title. (Year). Retrieved from <DOI>" names no authors; the parser puts the title in the
    # author position. The DOI resolves to that title, so the reference is verified.
    raw = f"{TITLE}. (2025). Retrieved from https://doi.org/10.1126/sciadv.adt3813"
    parsed = parse_references(raw + "\n")[0]
    assert parsed.authors and not parsed.title  # the parse this test is about
    client = fixture_client({"https://doi.org/10.1126/sciadv.adt3813": "kobak_doi"})
    verdict = verify_reference(parsed, [], client)
    assert verdict.status in {RefStatus.VERIFIED, RefStatus.VERIFIED_WITH_ERRORS}
    assert "authors_absent" in verdict.notes


def test_real_author_lists_are_never_mistaken_for_the_title():
    from proposalbench.evidence.match import MatchConfig, authors_are_title

    cfg = MatchConfig()
    assert not authors_are_title(["Smith", "Jones"], TITLE, cfg)
    assert authors_are_title(
        ["Delving into LLM-assisted writing in biomedical publications through excess vocabulary"],
        TITLE,
        cfg,
    )


def test_dossier_reference_with_compound_surnames_is_not_miscited(fixture_client):
    raw = (
        "Recuero Valdelomar, A. y Ledesma Corchero, P. (2021). «Redes de vecindad y "
        "envejecimiento en pueblos pequeños». Revista de Estudios Rurales Ibéricos, 28(3), 289–310."
    )
    pub = {
        "key": "recuero2021",
        "title": "Redes de vecindad y envejecimiento en pueblos pequeños",
        "authors": ["Recuero Valdelomar, A.", "Ledesma Corchero, P."],
        "year": 2021,
        "venue": "Revista de Estudios Rurales Ibéricos",
    }
    ref = parse_references(f"1. {raw}\n")[0]
    assert ref.authors == ["Recuero Valdelomar", "Ledesma Corchero"]
    verdict = verify_reference(ref, [pub], fixture_client({}))
    assert verdict.status == RefStatus.DOSSIER, verdict.notes


def test_compound_surname_without_initials_matches():
    assert author_overlap(["Recuero Valdelomar"], ["Recuero Valdelomar, A."]) == "first"
    assert author_overlap(["Smith"], ["Jones, A."]) == "none"
