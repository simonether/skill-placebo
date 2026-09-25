import numpy as np
import pytest

from skill_placebo.analysis import compare, holm, kill_test, verdict, verdicts


def make_arm(rng, n_tasks=20, reps=5, cost_scale=1.0, pass_shift=0.0, task_seed=1):
    """Tasks share difficulty and base cost across arms (task_seed), trial noise differs (rng)."""
    trng = np.random.default_rng(task_seed)
    base_cost = trng.uniform(0.1, 0.5, n_tasks)
    base_pass = trng.uniform(0.3, 0.7, n_tasks)
    arm = {}
    for t in range(n_tasks):
        p = min(1.0, max(0.0, base_pass[t] + pass_shift))
        arm[f"t{t:02d}"] = [
            (float(base_cost[t] * cost_scale * rng.lognormal(0, 0.3)), bool(rng.random() < p))
            for _ in range(reps)
        ]
    return arm


def test_point_estimates_exact():
    a = {"x": [(1.0, True), (1.0, False)], "y": [(3.0, True), (3.0, True)]}
    b = {"x": [(2.0, False), (2.0, False)], "y": [(2.0, True), (2.0, False)]}
    c = compare(a, b, n_boot=200)
    assert c.cost_treat == pytest.approx(2.0)
    assert c.cost_control == pytest.approx(2.0)
    assert c.ratio == pytest.approx(1.0)
    assert c.pass_treat == pytest.approx(0.75)
    assert c.pass_control == pytest.approx(0.25)
    assert c.diff_pp == pytest.approx(50.0)
    assert c.cost_per_solved_treat == pytest.approx(8.0 / 3)


def test_unpaired_tasks_ignored():
    a = {"x": [(1.0, True)], "only_a": [(9.0, True)]}
    b = {"x": [(1.0, False)], "only_b": [(9.0, False)]}
    c = compare(a, b, n_boot=100)
    assert c.n_tasks == 1 and c.cost_treat == 1.0


def test_detects_30pct_cheaper_skill():
    rng = np.random.default_rng(0)
    placebo = make_arm(rng)
    skill = make_arm(rng, cost_scale=0.7)
    c = compare(skill, placebo)
    assert 0.6 < c.ratio < 0.8
    assert c.ratio_ci[1] < 1.0
    assert c.ratio_p < 0.01
    assert verdict(c, c.ratio_p, c.diff_p) == "beats placebo"


def test_no_effect_is_no_better():
    rng = np.random.default_rng(1)
    placebo = make_arm(rng)
    skill = make_arm(rng)
    c = compare(skill, placebo)
    assert c.ratio_ci[0] < 1.0 < c.ratio_ci[1]
    assert verdict(c, c.ratio_p, c.diff_p) == "no better than placebo"


def test_pass_ci_width_about_14pp():
    """METHOD.md 9.2 claims a CI on D of about +-14 pp at 20 tasks x 5 trials."""
    rng = np.random.default_rng(2)
    widths = []
    for _ in range(5):
        c = compare(make_arm(rng), make_arm(rng))
        widths.append((c.diff_ci_pp[1] - c.diff_ci_pp[0]) / 2)
    assert 8 < float(np.mean(widths)) < 18


def test_holm():
    adj = holm({"a": 0.01, "b": 0.04, "c": 0.03})
    assert adj["a"] == pytest.approx(0.03)
    assert adj["c"] == pytest.approx(0.06)
    assert adj["b"] == pytest.approx(0.06)


def test_verdict_rules():
    class C:
        ratio = 0.8
        diff_pp = -20.0
    assert verdict(C, 0.01, 0.01) == "trade-off"
    assert verdict(C, 0.01, 0.5) == "beats placebo"
    assert verdict(C, 0.5, 0.01) == "worse than placebo"
    assert verdict(C, 0.5, 0.5) == "no better than placebo"


def test_verdicts_and_kill_test():
    rng = np.random.default_rng(3)
    placebo = make_arm(rng)
    comps = {
        "cheap": compare(make_arm(rng, cost_scale=0.6), placebo),
        "same": compare(make_arm(rng), placebo),
    }
    v = verdicts(comps)
    assert v["cheap"]["verdict"] == "beats placebo"
    assert v["same"]["verdict"] == "no better than placebo"
    assert kill_test(comps)["kill"] is False
    assert kill_test({"same": comps["same"]})["kill"] is True
