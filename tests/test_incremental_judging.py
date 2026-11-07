from proposalbench import evaluate
from proposalbench.judge.runner import ItemJudgment, JudgeRun
from proposalbench.llm import ModelSpec
from proposalbench.systems.base import Submission, SubmissionMeta
from proposalbench.tasks.loader import Repository


def test_new_items_are_judged_alone_and_merged(tmp_path, monkeypatch):
    repo = Repository()
    rt = repo.load_task(next(d for d in repo.task_dirs() if d.name == "pilot-nih-r21-persistence"))
    text = (
        "# P\n\n## Specific Aims\n\n" + "Aim text. " * 200 + "\n\n## Research Strategy\n\n"
        "### Significance\n\nS.\n\n### Innovation\n\nI.\n\n### Approach\n\nA.\n"
    )
    calls = []

    def fake_judge(spec, rt_, parsed, items):
        calls.append([i.id for i in items])
        judgments = [ItemJudgment(i.id, spec.model_id, "yes", [], "") for i in items]
        return JudgeRun(spec.model_id, judgments, [], 1, 1)

    monkeypatch.setattr(evaluate, "run_judge", fake_judge)
    monkeypatch.setattr(evaluate, "run_claims", lambda *a, **k: evaluate.ClaimsRun("j", [], ""))
    monkeypatch.setattr(evaluate, "extract_fact_sheet", lambda *a, **k: (None, {}))
    monkeypatch.setattr(evaluate, "build_pairs", lambda *a, **k: ([], {}))
    monkeypatch.setattr(evaluate, "verify_references", lambda *a, **k: [])  # no evidence calls
    spec = ModelSpec("bedrock", "zai.glm-5")
    sub = Submission(text, SubmissionMeta("s", "v", rt.id, "pilot", 1, "ok"))
    all_items = evaluate.items_for(rt)
    first = all_items[:-3]
    monkeypatch.setattr(evaluate, "items_for", lambda rt_: first)
    evaluate.evaluate_submission(rt, sub, tmp_path, [spec], tmp_path / "cache.sqlite")
    monkeypatch.setattr(evaluate, "items_for", lambda rt_: all_items)
    evaluate.evaluate_submission(rt, sub, tmp_path, [spec], tmp_path / "cache.sqlite")
    added = [i.id for i in all_items[-3:] if not evaluate._check_only(i)]
    assert calls[-1] == added
    run = evaluate._judge_run_from_dict(evaluate._load(tmp_path / "judges" / "zai.glm-5.json"))
    assert {j.item_id for j in run.judgments} >= set(added)


def test_missing_answers_are_retried_but_given_verdicts_are_kept(tmp_path, monkeypatch):
    repo = Repository()
    rt = repo.load_task(next(d for d in repo.task_dirs() if d.name == "pilot-nih-r21-persistence"))
    text = (
        "# P\n\n## Specific Aims\n\n" + "Aim text. " * 200 + "\n\n## Research Strategy\n\n"
        "### Significance\n\nS.\n\n### Innovation\n\nI.\n\n### Approach\n\nA.\n"
    )
    judged = [i for i in evaluate.items_for(rt) if not evaluate._check_only(i)]
    lost = {judged[0].id, judged[1].id}
    calls = []

    def fake_judge(spec, rt_, parsed, items):
        calls.append([i.id for i in items])
        first = len(calls) == 1
        judgments = [
            ItemJudgment(i.id, spec.model_id, "missing" if first and i.id in lost else "no")
            for i in items
        ]
        return JudgeRun(spec.model_id, judgments, [], 1, 1)

    monkeypatch.setattr(evaluate, "run_judge", fake_judge)
    monkeypatch.setattr(evaluate, "run_claims", lambda *a, **k: evaluate.ClaimsRun("j", [], ""))
    monkeypatch.setattr(evaluate, "extract_fact_sheet", lambda *a, **k: (None, {}))
    monkeypatch.setattr(evaluate, "build_pairs", lambda *a, **k: ([], {}))
    monkeypatch.setattr(evaluate, "verify_references", lambda *a, **k: [])
    spec = ModelSpec("bedrock", "zai.glm-5")
    sub = Submission(text, SubmissionMeta("s", "v", rt.id, "pilot", 1, "ok"))
    evaluate.evaluate_submission(rt, sub, tmp_path, [spec], tmp_path / "cache.sqlite")
    evaluate.evaluate_submission(rt, sub, tmp_path, [spec], tmp_path / "cache.sqlite")
    assert sorted(calls[-1]) == sorted(lost)
    run = evaluate._judge_run_from_dict(evaluate._load(tmp_path / "judges" / "zai.glm-5.json"))
    by_id = {j.item_id: j.verdict for j in run.judgments}
    assert len(run.judgments) == len(by_id)
    assert all(by_id[i] == "no" for i in lost)


def test_reworded_items_are_rejudged(tmp_path, monkeypatch):
    from proposalbench.judge.runner import item_digest

    repo = Repository()
    rt = repo.load_task(next(d for d in repo.task_dirs() if d.name == "pilot-nih-r21-persistence"))
    text = (
        "# P\n\n## Specific Aims\n\n" + "Aim text. " * 200 + "\n\n## Research Strategy\n\n"
        "### Significance\n\nS.\n\n### Innovation\n\nI.\n\n### Approach\n\nA.\n"
    )
    calls = []

    def fake_judge(spec, rt_, parsed, items):
        calls.append([i.id for i in items])
        judgments = [ItemJudgment(i.id, spec.model_id, "yes", [], "") for i in items]
        digests = {i.id: item_digest(i) for i in items}
        return JudgeRun(spec.model_id, judgments, [], 1, 1, digests)

    monkeypatch.setattr(evaluate, "run_judge", fake_judge)
    monkeypatch.setattr(evaluate, "run_claims", lambda *a, **k: evaluate.ClaimsRun("j", [], ""))
    monkeypatch.setattr(evaluate, "extract_fact_sheet", lambda *a, **k: (None, {}))
    monkeypatch.setattr(evaluate, "build_pairs", lambda *a, **k: ([], {}))
    monkeypatch.setattr(evaluate, "verify_references", lambda *a, **k: [])
    spec = ModelSpec("bedrock", "zai.glm-5")
    sub = Submission(text, SubmissionMeta("s", "v", rt.id, "pilot", 1, "ok"))
    items = evaluate.items_for(rt)
    evaluate.evaluate_submission(rt, sub, tmp_path, [spec], tmp_path / "cache.sqlite")
    target = next(i for i in items if not evaluate._check_only(i))
    reworded = [
        i.model_copy(update={"question": i.question + " (reworded)"}) if i is target else i
        for i in items
    ]
    monkeypatch.setattr(evaluate, "items_for", lambda rt_: reworded)
    evaluate.evaluate_submission(rt, sub, tmp_path, [spec], tmp_path / "cache.sqlite")
    assert calls[-1] == [target.id]
    evaluate.evaluate_submission(rt, sub, tmp_path, [spec], tmp_path / "cache.sqlite")
    assert len(calls) == 2  # the new wording's digest is stored: nothing left to re-judge


def test_results_of_a_regenerated_proposal_are_retired(tmp_path):
    from proposalbench.evaluate import _proposal_digest, _retire_if_regenerated

    out = tmp_path / "eval" / "sys" / "public" / "task" / "1"
    out.mkdir(parents=True)
    (out / "score.json").write_text("{}")
    _retire_if_regenerated(out, "first text")  # no stamp: trusted, left in place
    assert (out / "score.json").is_file()
    (out / "submission.sha256").write_text(_proposal_digest("first text"))
    _retire_if_regenerated(out, "first text")
    assert (out / "score.json").is_file()
    _retire_if_regenerated(out, "second text")
    assert not out.exists()
    moved = list((tmp_path / "eval" / "_stale").glob("*/sys/public/task/1/score.json"))
    assert len(moved) == 1
    assert not list((tmp_path / "eval").glob("*/*/*/*/score.json"))


def test_a_spent_source_defers_the_evaluation(tmp_path, monkeypatch):
    import pytest

    from proposalbench import evaluate

    class Client:
        def __init__(self, *a, **k):
            self.events = []
            self.unavailable_sources = {"api.openalex.org": "http_429, retry-after 9000s"}

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    monkeypatch.setattr(evaluate, "EvidenceClient", Client)
    monkeypatch.setattr(evaluate, "verify_references", lambda *a, **k: [])
    rt = Repository().get(Repository().task_dirs()[0].name)
    out = tmp_path / "e" / "s" / "pilot" / "t" / "1"
    sub = Submission("# Aims\n\nText.\n", SubmissionMeta("s", "v", rt.id, "pilot", 1, "ok"))
    with pytest.raises(evaluate.SourceUnavailable):
        evaluate.evaluate_submission(rt, sub, out, [], tmp_path / "cache.sqlite")
    assert not (out / "references.json").exists()
