"""Pre-registered analysis (METHOD.md sections 9 and 11).

All comparisons are within one harness and paired by task. A comparison takes two arms, each a
mapping task -> list of trials, where a trial is (cost_usd, passed). Only tasks present in both arms
are used.

Statistics:
  R = mean cost (treatment) / mean cost (control)
  D = pass rate (treatment) - pass rate (control), in percentage points
95% CIs and two-sided p-values come from a cluster bootstrap over tasks: resample tasks with
replacement (the same resampled tasks for both arms) and keep all trials of each resampled task.
Resampling trials again inside each task would count the within-task noise twice and inflate the
CI (tests/test_analysis.py::test_pass_ci_width_about_14pp).
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Mapping, Sequence

import numpy as np

Trial = tuple[float, bool]
Arm = Mapping[str, Sequence[Trial]]

N_BOOT = 10_000
SEED = 20260925
ALPHA = 0.05
KILL_BAND = (0.90, 1.10)


@dataclass
class Comparison:
    n_tasks: int
    n_treat: int
    n_control: int
    cost_treat: float
    cost_control: float
    pass_treat: float
    pass_control: float
    ratio: float
    ratio_ci: tuple[float, float]
    ratio_p: float
    diff_pp: float
    diff_ci_pp: tuple[float, float]
    diff_p: float
    cost_per_solved_treat: float | None
    cost_per_solved_control: float | None

    def as_dict(self) -> dict:
        return asdict(self)


def _pack(arm: Arm, tasks: list[str]):
    n = np.array([len(arm[t]) for t in tasks])
    width = int(n.max())
    cost = np.zeros((len(tasks), width))
    passed = np.zeros((len(tasks), width))
    for i, t in enumerate(tasks):
        for j, (c, p) in enumerate(arm[t]):
            cost[i, j] = c
            passed[i, j] = 1.0 if p else 0.0
    return cost, passed, n


def _resample_means(cost, passed, n, tidx):
    """Mean cost and pass rate for each bootstrap replicate. tidx: (B, T) resampled task rows."""
    width = cost.shape[1]
    mask = (np.arange(width)[None, :] < n[:, None]).astype(float)  # (T, W)
    task_cost = (cost * mask).sum(axis=1)
    task_pass = (passed * mask).sum(axis=1)
    denom = n[tidx].sum(axis=1)
    return task_cost[tidx].sum(axis=1) / denom, task_pass[tidx].sum(axis=1) / denom


def _two_sided_p(samples: np.ndarray, null: float) -> float:
    b = len(samples)
    lo = (np.count_nonzero(samples <= null) + 1) / (b + 1)
    hi = (np.count_nonzero(samples >= null) + 1) / (b + 1)
    return float(min(1.0, 2 * min(lo, hi)))


def compare(treat: Arm, control: Arm, n_boot: int = N_BOOT, seed: int = SEED) -> Comparison:
    tasks = sorted(set(treat) & set(control))
    tasks = [t for t in tasks if len(treat[t]) and len(control[t])]
    if not tasks:
        raise ValueError("no tasks with trials in both arms")
    ct, pt, nt = _pack(treat, tasks)
    cc, pc, nc = _pack(control, tasks)

    def point(cost, passed, n):
        mask = np.arange(cost.shape[1])[None, :] < n[:, None]
        k = mask.sum()
        return float((cost * mask).sum() / k), float((passed * mask).sum() / k), int(k)

    cost_t, pass_t, k_t = point(ct, pt, nt)
    cost_c, pass_c, k_c = point(cc, pc, nc)

    rng = np.random.default_rng(seed)
    tidx = rng.integers(0, len(tasks), size=(n_boot, len(tasks)))
    bc_t, bp_t = _resample_means(ct, pt, nt, tidx)
    bc_c, bp_c = _resample_means(cc, pc, nc, tidx)
    with np.errstate(divide="ignore", invalid="ignore"):
        ratios = bc_t / bc_c
    ratios = ratios[np.isfinite(ratios)]
    diffs = (bp_t - bp_c) * 100

    def solved(cost, passed_rate, k):
        n_pass = passed_rate * k
        return cost * k / n_pass if n_pass else None

    return Comparison(
        n_tasks=len(tasks),
        n_treat=k_t,
        n_control=k_c,
        cost_treat=cost_t,
        cost_control=cost_c,
        pass_treat=pass_t,
        pass_control=pass_c,
        ratio=cost_t / cost_c if cost_c else float("nan"),
        ratio_ci=(float(np.quantile(ratios, 0.025)), float(np.quantile(ratios, 0.975))),
        ratio_p=_two_sided_p(ratios, 1.0),
        diff_pp=(pass_t - pass_c) * 100,
        diff_ci_pp=(float(np.quantile(diffs, 0.025)), float(np.quantile(diffs, 0.975))),
        diff_p=_two_sided_p(diffs, 0.0),
        cost_per_solved_treat=solved(cost_t, pass_t, k_t),
        cost_per_solved_control=solved(cost_c, pass_c, k_c),
    )


def holm(pvalues: Mapping[str, float]) -> dict[str, float]:
    """Holm-Bonferroni adjusted p-values (monotone), keyed like the input."""
    items = sorted(pvalues.items(), key=lambda kv: kv[1])
    m = len(items)
    out, running = {}, 0.0
    for i, (key, p) in enumerate(items):
        running = max(running, min(1.0, (m - i) * p))
        out[key] = running
    return out


def verdict(cmp: Comparison, ratio_p_adj: float, diff_p_adj: float, alpha: float = ALPHA) -> str:
    """METHOD.md 9.1. Cost improves when R < 1, pass improves when D > 0."""
    cost_better = ratio_p_adj < alpha and cmp.ratio < 1
    cost_worse = ratio_p_adj < alpha and cmp.ratio > 1
    pass_better = diff_p_adj < alpha and cmp.diff_pp > 0
    pass_worse = diff_p_adj < alpha and cmp.diff_pp < 0
    better = cost_better or pass_better
    worse = cost_worse or pass_worse
    if better and not worse:
        return "beats placebo"
    if better and worse:
        return "trade-off"
    if worse:
        return "worse than placebo"
    return "no better than placebo"


def verdicts(skill_vs_placebo: Mapping[str, Comparison], alpha: float = ALPHA) -> dict[str, dict]:
    """Holm across skills within one harness, separately for cost and pass, then 9.1 verdicts."""
    adj_r = holm({k: c.ratio_p for k, c in skill_vs_placebo.items()})
    adj_d = holm({k: c.diff_p for k, c in skill_vs_placebo.items()})
    return {
        k: {
            "verdict": verdict(c, adj_r[k], adj_d[k], alpha),
            "ratio_p_adj": adj_r[k],
            "diff_p_adj": adj_d[k],
            **c.as_dict(),
        }
        for k, c in skill_vs_placebo.items()
    }


def kill_test(skill_vs_placebo: Mapping[str, Comparison], band: tuple[float, float] = KILL_BAND) -> dict:
    """METHOD.md 11: stop if no skill has R outside the band with a 95% CI excluding 1."""
    nontrivial = {
        k: c.ratio
        for k, c in skill_vs_placebo.items()
        if (c.ratio < band[0] or c.ratio > band[1]) and not (c.ratio_ci[0] <= 1.0 <= c.ratio_ci[1])
    }
    return {"kill": not nontrivial, "nontrivial": nontrivial}
