import json
from pathlib import Path

import pytest

from proposalbench.report import costs
from proposalbench.report.leaderboard import leaderboard, to_markdown

PRICES = {
    "m": costs.Price(input=2.0, cached_input=0.2, output=10.0),
    "judge-a": costs.Price(input=1.0, cached_input=1.0, output=4.0),
}


def _meta(**kw) -> dict:
    return {
        "models": [
            {
                "model_id": "m",
                "family": "f",
                "input_tokens": 1_000_000,
                "output_tokens": 100_000,
                **kw.pop("usage", {}),
            }
        ],
        **kw,
    }


def test_recorded_cost_wins():
    c = costs.generation_cost(_meta(cost_usd=1.27), PRICES)
    assert c == costs.Cost(1.27, "recorded")


def test_estimate_from_tokens_and_cache_hits():
    assert costs.generation_cost(_meta(), PRICES) == costs.Cost(3.0, "estimated")
    cached = costs.generation_cost(_meta(usage={"cached_input_tokens": 500_000}), PRICES)
    assert cached == costs.Cost(
        round((500_000 * 2.0 + 500_000 * 0.2 + 100_000 * 10.0) / 1e6, 4), "estimated"
    )


def test_codex_without_cache_split_is_an_upper_bound():
    assert costs.generation_cost(_meta(), PRICES, tool="codex").basis == "upper_bound"
    split = _meta(usage={"cached_input_tokens": 0})
    assert costs.generation_cost(split, PRICES, tool="codex").basis == "estimated"


def test_unknown_cost_without_tokens_or_price():
    assert costs.generation_cost({"models": []}, PRICES) == costs.Cost(None, None)
    unpriced = {"models": [{"model_id": "x", "input_tokens": 5, "output_tokens": 5}]}
    assert costs.generation_cost(unpriced, PRICES) == costs.Cost(None, None)


def _write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))


def _judged(d: Path, *, claims_tokens: bool = True) -> None:
    _write(
        d / "judges" / "judge-a.json",
        {"judge": "judge-a", "input_tokens": 1_000_000, "output_tokens": 0},
    )
    claims = {"judge": "judge-a", "claims": [], "raw": ""}
    if claims_tokens:
        claims |= {"input_tokens": 0, "output_tokens": 250_000}
    _write(d / "claims" / "judge-a.json", claims)
    _write(d / "claims_adjudication" / "candidates.json", {"candidates": []})
    _write(
        d / "factsheet" / "judge-a.json",
        {"sheet": None, "record": {"input_tokens": 1_000_000, "output_tokens": 0}},
    )
    _write(d / "factsheet" / "merged.json", {"sheet": {}})


def test_judging_cost_sums_every_stage(tmp_path):
    _judged(tmp_path)
    assert costs.judging_cost(tmp_path, PRICES) == 3.0


def test_judging_cost_unknown_when_a_stage_predates_token_recording(tmp_path):
    _judged(tmp_path, claims_tokens=False)
    assert costs.judging_cost(tmp_path, PRICES) is None


def test_weakest_basis():
    assert costs.weakest(["recorded", "upper_bound", "estimated"]) == "upper_bound"
    assert costs.weakest([None]) is None


def test_prices_file_covers_the_models_in_the_configs():
    prices = costs.load_prices()
    for model in (
        "claude-opus-5-5",
        "gpt-6-astra",
        "gemini-3.1-pro-preview",
        "us.moonshotai.kimi-k3",
        "zai.glm-5",
        "deepseek.v3.2",
    ):
        assert model in prices


@pytest.fixture
def run(tmp_path):
    results, subs = tmp_path / "results", tmp_path / "submissions"
    task = "pub2-aei-care-close"
    score = {
        "task": task,
        "sample": 1,
        "scorecard": {
            "score": 80.0,
            "quality": 85.0,
            "admissible": True,
            "has_critical": False,
            "components": {"call_responsiveness": 80.0, "substance": 80.0, "grounding": 90.0},
        },
        "counted_words": 1000,
        "references": {"verified": 3, "not_found": 1},
    }
    for system, meta in (
        (
            "direct-gemini-3.1-pro",
            {
                "wall_time_s": 120,
                "models": [
                    {
                        "model_id": "gemini-3.1-pro-preview",
                        "family": "google",
                        "input_tokens": 10_000,
                        "output_tokens": 10_000,
                    }
                ],
            },
        ),
        (
            "cli-codex-gpt-6-astra",
            {
                "wall_time_s": 600,
                "models": [
                    {
                        "model_id": "gpt-6-astra",
                        "family": "openai",
                        "input_tokens": 100_000,
                        "output_tokens": 10_000,
                    }
                ],
            },
        ),
    ):
        d = Path(system) / "public" / task / "1"
        _write(results / d / "score.json", {**score, "system": system})
        _write(subs / d / "meta.json", meta)
    _write(results / "judging_cost.json", {"per_evaluation_usd": 2.42})
    return results, subs


def test_leaderboard_reports_time_and_costs(run):
    results, subs = run
    rows = {r.system: r for r in leaderboard(results, subs)}
    gemini, codex = rows["direct-gemini-3.1-pro"], rows["cli-codex-gpt-6-astra"]
    assert (gemini.gen_minutes, gemini.gen_cost, gemini.gen_cost_basis) == (2.0, 0.14, "estimated")
    assert not gemini.subscription
    assert (codex.gen_cost, codex.gen_cost_basis, codex.subscription) == (1.5, "upper_bound", True)
    assert (gemini.judge_cost, gemini.judge_cost_basis) == (2.42, "run_average")
    table = to_markdown(list(rows.values()))
    assert "$0.14 est." in table and "≤$1.50 est. †" in table and "$2.42 avg" in table
