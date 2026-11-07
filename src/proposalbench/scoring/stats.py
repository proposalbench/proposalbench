"""Variance components from pilot results and the minimum detectable difference (MDE).

For a paired comparison of two systems on the same tasks, the per-task difference of their mean
scores has variance  sigma_task^2 + 2 * sigma_sample^2 / k, where sigma_task is the spread of
true differences across tasks (system-by-task interaction) and sigma_sample the spread between
repeated samples of one system on one task. With n independent tasks (the sealed split uses
unique calls and dossiers), MDE = (z_{1-alpha/2} + z_{power}) * sqrt(var / n).
"""

from __future__ import annotations

import math
from collections import defaultdict
from itertools import combinations
from statistics import NormalDist, mean, variance


def sample_sd(scores: dict[tuple[str, str], list[float]]) -> float | None:
    """Pooled SD between repeated samples of the same system on the same task."""
    num, den = 0.0, 0
    for vals in scores.values():
        if len(vals) > 1:
            num += variance(vals) * (len(vals) - 1)
            den += len(vals) - 1
    return math.sqrt(num / den) if den else None


def task_difference_sd(scores: dict[tuple[str, str], list[float]], k: int) -> float | None:
    """SD of true per-task differences between systems, after removing sample noise."""
    by_system: dict[str, dict[str, float]] = defaultdict(dict)
    for (system, task), vals in scores.items():
        by_system[system][task] = mean(vals)
    s_sample = sample_sd(scores) or 0.0
    estimates = []
    for a, b in combinations(sorted(by_system), 2):
        tasks = sorted(set(by_system[a]) & set(by_system[b]))
        if len(tasks) < 2:
            continue
        diffs = [by_system[a][t] - by_system[b][t] for t in tasks]
        estimates.append(max(0.0, variance(diffs) - 2 * s_sample**2 / k))
    return math.sqrt(mean(estimates)) if estimates else None


def mde(
    sd_task: float,
    sd_sample: float,
    k: int,
    n_tasks: int,
    alpha: float = 0.05,
    power: float = 0.8,
    comparisons: int = 1,
) -> float:
    """Smallest true difference detected with the given power (Bonferroni over comparisons,
    a conservative stand-in for Holm)."""
    z = NormalDist().inv_cdf(1 - alpha / (2 * comparisons)) + NormalDist().inv_cdf(power)
    return z * math.sqrt((sd_task**2 + 2 * sd_sample**2 / k) / n_tasks)


def tasks_needed(target: float, sd_task: float, sd_sample: float, k: int, **kw) -> int:
    n = 2
    while mde(sd_task, sd_sample, k, n, **kw) > target and n < 1000:
        n += 1
    return n
