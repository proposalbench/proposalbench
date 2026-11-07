from pathlib import Path
from types import SimpleNamespace

from proposalbench.report import export


class _Repo:
    """Each task has its own call and dossier, so the bootstrap is a plain task bootstrap."""

    def get(self, task_id):
        return SimpleNamespace(
            call=SimpleNamespace(id=f"c-{task_id}"), dossier=SimpleNamespace(id=f"d-{task_id}")
        )


def test_paired_difference_on_common_tasks_only():
    a = {"t1": 90.0, "t2": 80.0, "t3": 70.0, "extra": 10.0}
    b = {"t1": 85.0, "t2": 82.0, "t3": 70.0}
    r = export.paired(a, b, _Repo())
    assert (r["n"], r["diff"], r["wins"], r["ties"], r["losses"]) == (3, 1.0, 1, 1, 1)
    assert r["ci_low"] <= r["diff"] <= r["ci_high"]
    assert export.paired({"x": 1.0}, {"y": 1.0}, _Repo()) == {"n": 0}


def test_release_views():
    rel = export.Release(
        eval_id="e",
        release="r",
        title="t",
        judge_panel="p",
        systems={"pro": {}, "other": {}},
        headline_system="pro",
        headline_tasks=["t1"],
        featured_schemes=[],
    )
    s = lambda system, task, sample: {"system": system, "task": task, "sample": sample}  # noqa: E731
    assert rel.headline(s("other", "t1", 1)) and not rel.headline(s("other", "t1", 2))
    assert not rel.headline(s("other", "t2", 1)) and not rel.published(s("dropped", "t1", 1))
    assert rel.full(s("other", "t2", 2)) and not rel.full(s("pro", "t1", 1))


def test_consistency_needs_both_samples():
    def sample(system, task, k, score):
        return (
            Path("."),
            {"system": system, "task": task, "sample": k, "scorecard": {"score": score}},
        )

    rows = [sample("a", f"t{i}", k, 80.0 + i + (k == 2)) for i in range(4) for k in (1, 2)]
    rows.append(sample("b", "t0", 1, 50.0))
    out = export._consistency(rows)
    assert set(out) == {"a"} and out["a"]["n"] == 4 and out["a"]["mean_abs_diff"] == 1.0


def test_macro_names_are_letters_only():
    assert export.macro_name("headline", "direct-codex-gpt-6-sol", "score") == (
        "pbHeadlineDirectCodexGptSixSolScore"
    )
    assert export.macro_name("versus", "direct-cc-claude-opus-5.5", "ci").isalpha()


def test_models_prefer_the_resolved_names_in_notes():
    meta = {"notes": ["models used: claude-opus-5-5"], "models": [{"model_id": "opus"}]}
    assert export._models(meta) == ["claude-opus-5-5"]
    assert export._models({"models": [{"model_id": "gpt-6-astra"}]}) == ["gpt-6-astra"]


def test_numbers_tex_has_one_macro_per_figure():
    row = {
        "system": "pro",
        "score": 96.56,
        "ci_low": 94.6,
        "ci_high": 97.95,
        "samples": 34,
        "gen_minutes": 13.2,
        "gen_cost": 3.15,
    }
    data = {
        "meta": {
            "release": "r",
            "headline_tasks": ["t"] * 34,
            "development_tasks": ["d"] * 26,
            "tasks_in_split": 60,
        },
        "systems": {"pro": {}},
        "headline": {"leaderboard": [row], "versus_headline": {}},
        "full": {"leaderboard": []},
        "judges": {"measured": {"mean_usd": 2.92}},
    }
    tex = export.numbers_tex(data)
    assert "\\newcommand{\\pbHeadlineProScore}{96.6}" in tex
    assert "\\newcommand{\\pbHeadlineTasks}{34}" in tex and "\\pbJudgeCostMean}{2.92}" in tex


def _score(refs, support, defects, traps):
    return {
        "references": refs,
        "support": {"counts": support},
        "scorecard": {"defects": [{"kind": k} for k in defects]},
        "items": [
            {"item_id": f"TRAP-T{i}", "status": "scored", "score": s} for i, s in enumerate(traps)
        ],
    }


def test_granular_counts_and_pooled_metrics():
    a = export.granular(
        _score(
            {"verified": 8, "not_found": 1, "doi_unresolved": 1, "dossier": 3},
            {"supports": 6, "partial": 2, "unrelated": 1, "contradicts": 1, "cannot_tell": 5},
            ["applicant_unsupported", "applicant_contradicted_minor", "metadata_dossier_miscited"],
            [1.0, 0.0],
        ),
        {"em_dashes_per_1k": 2.0},
    )
    assert (a["ext_refs"], a["refs_unverifiable"], a["refs_fabricated"]) == (10, 2, 1)
    assert (a["cites_checked"], a["cites_supported"], a["cites_unsupported"]) == (10, 6, 2)
    assert (a["applicant_claims"], a["dossier_miscited"], a["traps_score"]) == (2, 1, 0.5)
    b = export.granular(_score({"verified": 30}, {}, [], []), {})
    rows = [
        {"system": "s", "admissible": True, **a},
        {"system": "s", "admissible": False, **b},
    ]
    m = export.metrics(rows)["s"]
    # Pooled over references: 2 unverifiable of 40, not the mean of 0.2 and 0.
    assert m["unverifiable_refs"] == 0.05 and m["refs_per_proposal"] == 20
    assert m["traps_caught"] == 0.5 and m["rejected"] == 0.5 and m["em_dashes_per_1k"] == 2.0


def test_undisclosed_cost_is_never_published():
    from proposalbench.report.leaderboard import Row

    rel = export.Release(
        eval_id="e",
        release="r",
        title="t",
        judge_panel="p",
        systems={"pro": {"name": "Pro"}},
        headline_system="pro",
        headline_tasks=[],
        featured_schemes=[],
        undisclosed_cost=["pro"],
    )
    row = Row("pro", 1, 90.0, 89.0, 91.0, 90.0, {}, 1.0, 0.0, 0.9, 0.9, 0.0, 10.0, 3.15, "recorded")
    out = export._rows([row], rel)[0]
    assert out["gen_cost"] is None and out["gen_cost_basis"] == export.NOT_DISCLOSED
    assert export._usd(None, export.NOT_DISCLOSED, False) == "not disclosed"
