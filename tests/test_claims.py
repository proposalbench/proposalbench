import pytest

from proposalbench.judge import claims as C
from proposalbench.judge.claims import AdjudicationRun, Claim, ClaimsRun
from proposalbench.llm import Completion, ModelSpec
from proposalbench.tasks.loader import Repository

Q1 = "The PI received the Zorvellan Prize in 2025."
Q2 = "The team holds a panel survey of 410 farms."


def _runs():
    return [
        ClaimsRun("a", [Claim(Q1, "unsupported", "critical")], ""),
        ClaimsRun("b", [Claim(Q2, "unsupported", "minor")], ""),
        ClaimsRun("c", [], ""),
    ]


def _adj(judge, verdicts, quotes=(Q1, Q2)):
    return AdjudicationRun(judge, verdicts, "", quotes=list(quotes))


def test_candidates_pool_every_judge():
    assert [c.quote for c in C.candidates(_runs())] == [Q1, Q2]


def test_majority_of_rulings_decides():
    cands = C.candidates(_runs())
    runs = [
        _adj("a", {"0": "critical", "1": "supported"}),
        _adj("b", {"0": "critical", "1": "minor"}),
        _adj("c", {"0": "critical", "1": "supported"}),
    ]
    agreed = C.adjudicated_consensus(cands, runs)
    assert [(c.quote, c.severity, c.judges) for c in agreed] == [(Q1, "critical", ["a", "b", "c"])]


def test_disputed_critical_is_minor():
    cands = C.candidates(_runs())
    runs = [
        _adj("a", {"0": "critical"}),
        _adj("b", {"0": "critical"}),
        _adj("c", {"0": "supported"}),
    ]
    assert [c.severity for c in C.adjudicated_consensus(cands, runs)] == ["minor"]


def test_flagged_but_not_mostly_critical_is_minor():
    cands = C.candidates(_runs())
    runs = [
        _adj("a", {"0": "critical"}),
        _adj("b", {"0": "minor"}),
        _adj("c", {"0": "minor"}),
    ]
    assert [c.severity for c in C.adjudicated_consensus(cands, runs)] == ["minor"]


def test_too_few_valid_rulings_is_never_a_defect():
    cands = C.candidates(_runs())
    runs = [_adj("a", {"0": "critical"}), _adj("b", {}), _adj("c", {})]
    assert C.adjudicated_consensus(cands, runs) == []


def test_rulings_on_another_candidate_list_are_rejected():
    cands = C.candidates(_runs())
    with pytest.raises(ValueError):
        C.adjudicated_consensus(cands, [_adj("a", {"0": "critical"}, quotes=[Q2])])


def test_adjudicate_parses_one_call(monkeypatch):
    rt = Repository().load_task(Repository().task_dirs()[0])
    calls = []

    def fake(spec, messages, system=None, max_tokens=None):
        calls.append(messages[0]["content"])
        text = '{"verdicts": [{"id": 1, "verdict": "Critical"}, {"id": 2, "verdict": "odd"}]}'
        return Completion(text, spec.model_id, 10, 5, "end", 0.1)

    monkeypatch.setattr(C, "complete", fake)
    run = C.adjudicate(ModelSpec("bedrock", "zai.glm-5"), rt, "text", C.candidates(_runs()))
    assert run.verdicts == {"0": "critical"} and run.quotes == [Q1, Q2]
    assert len(calls) == 1 and Q1 in calls[0] and "1. " in calls[0]
    empty = C.adjudicate(ModelSpec("bedrock", "zai.glm-5"), rt, "text", [])
    assert empty.verdicts == {} and len(calls) == 1


def test_applicant_sources_include_the_brief_with_precedence():
    repo = Repository()
    rt = repo.load_task(next(d for d in repo.task_dirs() if d.name == "pilot-he-soilwater-close"))
    text = C.applicant_sources(rt)
    assert '<file name="brief.md">' in text and C.BRIEF_NOTE in text
    assert all(f'<file name="{p}">' in text for p in rt.dossier_texts())
