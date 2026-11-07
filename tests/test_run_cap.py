from types import SimpleNamespace

from proposalbench.cli import new_spend, run_capped


def _one(cost):
    def one(tid, k):
        return tid, k, SimpleNamespace(cost_usd=cost)

    return one


def test_no_cap_runs_everything():
    seen = []
    spent, left = run_capped(
        [("a", 1), ("b", 1), ("c", 1)], _one(4.0), 2, None, 6.0, lambda *a: seen.append(a[0])
    )
    assert (sorted(seen), spent, left) == (["a", "b", "c"], 12.0, 0)


def test_cap_stops_starting_jobs_before_it_can_be_passed():
    jobs = [(str(i), 1) for i in range(20)]
    spent, left = run_capped(jobs, _one(4.0), 4, 30.0, 6.0, lambda *a: None)
    # Every start keeps recorded cost + 6 per running job within 30.
    assert spent <= 30.0 and left > 0 and spent + left * 4.0 == 80.0


def test_unknown_cost_counts_the_estimate():
    spent, left = run_capped([("a", 1), ("b", 1)], _one(None), 1, 7.0, 6.0, lambda *a: None)
    assert (spent, left) == (6.0, 1)


def test_custom_cost_reads_any_result_shape():
    seen = []
    spent, left = run_capped(
        [("a",), ("b",)],
        lambda x: ({"task": x}, 2.5),
        1,
        4.0,
        2.0,
        lambda s, c: seen.append(c),
        cost=lambda r: r[1],
    )
    assert (seen, spent, left) == ([2.5], 2.5, 1)


def test_evaluation_spend_counts_only_new_stages():
    assert new_spend(None, 3.0) == 3.0
    assert new_spend(3.0, 3.0) == 0.0  # everything reused from an earlier pass
    assert new_spend(1.0, 3.5) == 2.5
    assert new_spend(1.0, None) is None
