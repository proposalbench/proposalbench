from proposalbench.evidence.records import WorkRecord
from proposalbench.evidence.verify import ReferenceVerdict, RefStatus
from proposalbench.judge.support import Pair, SupportRun, _match_refs, consensus
from proposalbench.parse.references import ParsedReference


def _verdict(label, authors, year, status=RefStatus.VERIFIED):
    ref = ParsedReference(0, label, "raw", year=year, title="T", authors=authors)
    best = WorkRecord(
        "crossref", "x", None, "T", authors, year, None, "journal_article", None, None, {}
    )
    return ReferenceVerdict(ref, status, True, best)


def test_match_numeric_and_author_year():
    vs = [_verdict("1", ["García"], 2019), _verdict("2", ["Smith", "Lee"], 2020)]
    assert _match_refs(("2",), "numeric", vs) == [1]
    assert _match_refs(("garcia|2019a",), "author_year", vs) == [0]
    assert _match_refs(("smith|2021",), "author_year", vs) == []


def test_consensus_counts_reference_once_and_needs_majority():
    pairs = [
        Pair("p1", "s1", 0, "T", "A"),
        Pair("p2", "s2", 0, "T", "A"),
        Pair("p3", "s3", 1, "T", "A"),
    ]
    runs = [
        SupportRun("j1", {"p1": "unrelated", "p2": "unrelated", "p3": "contradicts"}),
        SupportRun("j2", {"p1": "unrelated", "p2": "unrelated", "p3": "supports"}),
        SupportRun("j3", {"p1": "supports", "p2": "unrelated", "p3": "cannot_tell"}),
    ]
    out = consensus(pairs, runs)
    assert [d["ref_index"] for d in out["defects"]] == [0]
    assert out["per_pair"]["p3"] == "no_majority"


def test_citation_dump_counts_three_references():
    from proposalbench.evaluate import deterministic_metrics
    from proposalbench.judge.support import cited_reference_indices

    vs = [_verdict(str(i), ["Author"], 2020) for i in range(1, 13)]
    dump = "Related work exists on many topics [1-10]. Soil water matters for yields [11]. "
    assert cited_reference_indices(dump, vs) == {0, 1, 2, 10}
    spread = " ".join(f"Finding number {i} is reported elsewhere [{i}]." for i in range(1, 11))
    assert len(cited_reference_indices(spread, vs)) == 10
    m = deterministic_metrics(vs, 1000, dump)
    assert m["verified_external_references"] == 4 and m["listed_verified_references"] == 12
    # References the panel found unrelated to their citing sentence do not count.
    assert deterministic_metrics(vs, 1000, dump, {0, 1})["verified_external_references"] == 2
