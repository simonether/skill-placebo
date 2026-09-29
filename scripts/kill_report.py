#!/usr/bin/env python3
"""Kill test (METHOD.md 11.3): cost ratio R and pass difference D of each kill-test skill vs its placebo.

  scripts/kill_report.py --harness claude-code
Uses, per trial, its last attempt; attempts where the arm did not reach the agent or that failed on
infrastructure are excluded. Writes results/pilot/kill-<harness>.json.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from skill_placebo.analysis import compare, kill_test  # noqa: E402
from skill_placebo.arms import claude_arms, codex_arms, PRIORITY, placebo_bucket_of  # noqa: E402
from skill_placebo.collect import trial_row  # noqa: E402
from skill_placebo.runner import arm_not_applied, infra_failure  # noqa: E402
import pilot  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--harness", default="claude-code")
    a = ap.parse_args()
    arms = claude_arms(PRIORITY) if a.harness == "claude-code" else codex_arms(PRIORITY)
    base = ROOT / "jobs" / "pilot" / a.harness / "kill"
    by_arm: dict[str, dict[str, list]] = {}
    excluded = []
    jobs = {}
    for d in sorted(base.glob("b*__*")):
        if d.is_dir():
            jobs.setdefault(d.name.split("__r")[0], []).append(d)
    for bname, attempts in jobs.items():
        last = sorted(attempts, key=lambda p: (len(p.name), p.name))[-1]
        arm = bname.split("__")[2]
        why = infra_failure(last) or arm_not_applied(last, arms[arm])
        if why:
            excluded.append({"job": last.name, "reason": why})
            continue
        for res in last.glob("*/result.json"):
            r = trial_row(res)
            if r and r["passed"] is not None:
                by_arm.setdefault(arm, {}).setdefault(r["task"], []).append((r["cost_est_usd"], bool(r["passed"]), r["units"], r["n_output"]))
    comps, table = {}, {}
    for skill in pilot.KILL_SKILLS[a.harness]:
        s_arm, p_arm = f"skill-{skill}", f"placebo-{placebo_bucket_of(skill, a.harness)}"
        if s_arm not in by_arm or p_arm not in by_arm:
            continue
        treat = {t: [(c, p) for c, p, _, _ in v] for t, v in by_arm[s_arm].items()}
        ctrl = {t: [(c, p) for c, p, _, _ in v] for t, v in by_arm[p_arm].items()}
        c = compare(treat, ctrl)
        comps[skill] = c
        out_t = sum(o for v in by_arm[s_arm].values() for *_, o in v) / sum(len(v) for v in by_arm[s_arm].values())
        out_c = sum(o for v in by_arm[p_arm].values() for *_, o in v) / sum(len(v) for v in by_arm[p_arm].values())
        table[skill] = {"placebo": p_arm, **c.as_dict(), "mean_output_tokens_skill": out_t, "mean_output_tokens_placebo": out_c}
        print(f"{skill:14s} vs {p_arm:14s} R={c.ratio:.2f} [{c.ratio_ci[0]:.2f}, {c.ratio_ci[1]:.2f}] "
              f"${c.cost_treat:.3f} vs ${c.cost_control:.3f}; pass {c.pass_treat:.0%} vs {c.pass_control:.0%}; "
              f"output tok {out_t:.0f} vs {out_c:.0f}; n={c.n_treat}/{c.n_control} over {c.n_tasks} tasks")
    k = kill_test(comps)
    print("kill:", k["kill"], "non-trivial:", k["nontrivial"])
    print("excluded attempts:", excluded)
    out = ROOT / "results" / "pilot" / f"kill-{a.harness}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"harness": a.harness, "comparisons": table, "kill": k, "excluded": excluded}, indent=1) + "\n")


if __name__ == "__main__":
    main()
