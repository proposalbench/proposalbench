import math

from proposalbench.scoring.stats import mde, sample_sd, task_difference_sd, tasks_needed


def test_sample_sd_pools_repeats():
    scores = {("a", "t1"): [10.0, 12.0], ("a", "t2"): [20.0, 22.0], ("b", "t1"): [5.0]}
    assert math.isclose(sample_sd(scores), math.sqrt(2.0))


def test_task_difference_sd_removes_sample_noise():
    scores = {
        ("a", "t1"): [60.0, 60.0],
        ("b", "t1"): [50.0, 50.0],
        ("a", "t2"): [70.0, 70.0],
        ("b", "t2"): [50.0, 50.0],
        ("a", "t3"): [80.0, 80.0],
        ("b", "t3"): [50.0, 50.0],
    }
    assert math.isclose(task_difference_sd(scores, k=2), 10.0)


def test_mde_shrinks_with_tasks_and_tasks_needed_is_consistent():
    assert mde(10, 5, 2, 40) < mde(10, 5, 2, 10)
    n = tasks_needed(6.0, 10, 5, 2)
    assert mde(10, 5, 2, n) <= 6.0 < mde(10, 5, 2, n - 1)
