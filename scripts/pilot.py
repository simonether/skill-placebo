#!/usr/bin/env python3
"""Pilot steps (METHOD.md section 11). One step per call, so each can be checked before the next.

  scripts/pilot.py token-check --harness claude-code   one trivial prompt per arm (section 4.1)
  scripts/pilot.py token-recheck --harness claude-code one trivial prompt per rescaled placebo
  scripts/pilot.py selection   --harness claude-code   pool tasks x 2 in the baseline arm (section 6)
  scripts/pilot.py selection   --harness codex         pool tasks x 1 in the baseline arm
  scripts/pilot.py kill        --harness claude-code   kill-test skills and their placebos (section 11)
  scripts/pilot.py collect                             jobs/pilot -> results/pilot/trials.csv
Add --dry-run to print the Harbor commands without running anything. Real runs need --units-budget
(the threshold for 25% of the weekly limit, METHOD.md amendment 2), plus --window-start,
--pace-units-5h and, at checkpoints, --stop-after.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from skill_placebo.arms import PRIORITY, claude_arms, codex_arms, mounts, placebo_bucket_of  # noqa: E402
from skill_placebo.collect import write_csv  # noqa: E402
from skill_placebo.harnesses import HARNESSES  # noqa: E402
from skill_placebo.runner import plan, run_batch  # noqa: E402

SEED = 20260928
KILL_SKILLS = {"claude-code": ["caveman", "ponytail", "i-have-adhd"],
               "codex": ["ponytail", "agent-skills", "compound-engineering"]}
PILOT_CAP = {"claude-code": 160, "codex": 100}  # amendment 7: 160 task trials on Claude Code


def pool_tasks() -> list[str]:
    """Pool tasks that passed the oracle 2/2 (tasks/pool/ORACLE.md is the record)."""
    manifest = json.loads((ROOT / "tasks" / "pool" / "manifest.json").read_text())
    failed = set(json.loads((ROOT / "tasks" / "pool" / "oracle_failed.json").read_text())) \
        if (ROOT / "tasks" / "pool" / "oracle_failed.json").exists() else set()
    return [f"pool/{t['source']}/{t['name']}" for t in manifest["tasks"] if f"{t['source']}/{t['name']}" not in failed]


def selection_outcomes(harness: str) -> dict[str, list[int]]:
    """task name -> pass flags of its baseline selection trials (infrastructure failures excluded)."""
    from skill_placebo.collect import trial_row
    out: dict[str, list[int]] = {}
    for st in ("selection", "selection-extra", "third"):
        for res in (ROOT / "jobs" / "pilot" / harness / st).glob("*/*/result.json"):
            r = trial_row(res)
            if r and not r["infra_failure"] and r["passed"] is not None:
                out.setdefault(r["task"], []).append(r["passed"])
    return out


def third_trial_tasks(harness: str, limit: int = 5) -> list[str]:
    """Tasks at 0/2 or 2/2 in the seeded order (round robin over sources: SWE-bench, TB2.1, TBLite),
    first `limit` of them (METHOD.md section 6 rule 2, section 11.1, amendment 6)."""
    order = json.loads((ROOT / "tasks" / "pilot_plan.json").read_text())["seeded_order"]
    outcomes = selection_outcomes(harness)
    seq, i = [], 0
    srcs = ["swebench-verified", "terminal-bench-2-1", "openthoughts-tblite"]
    while any(i < len(order[s]) for s in srcs):
        for s in srcs:
            if i < len(order[s]):
                seq.append(order[s][i])
        i += 1
    pick = []
    for t in seq:
        o = outcomes.get(t.split("/")[-1], [])
        if len(o) == 2 and sum(o) in (0, 2):
            pick.append(f"pool/{t}")
        if len(pick) == limit:
            break
    return pick


def arms_for(harness: str):
    return claude_arms(PRIORITY) if harness == "claude-code" else codex_arms(PRIORITY)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["token-check", "token-recheck", "selection", "selection-extra", "third", "kill", "collect"])
    ap.add_argument("--harness", choices=list(HARNESSES), default="claude-code")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--concurrency", type=int, default=2)
    ap.add_argument("--units-budget", type=float, help="stop when the ledger's limit units since --window-start reach this (the 25%%-of-week threshold)")
    ap.add_argument("--window-start", help="UTC time of the plan's last weekly reset, e.g. 2026-09-28T10:00:00Z")
    ap.add_argument("--pace-units-5h", type=float, help="never start a trial while the trailing 5 hours hold this many units")
    ap.add_argument("--stop-after", type=int, help="stop after this many trials complete (checkpoint)")
    ap.add_argument("--codex-weekly-start", type=float, help="Codex plan's weekly used %% before the benchmark")
    ap.add_argument("--usd-budget", type=float, help="stop when the ledger's $ equivalent since --window-start reaches this")
    ap.add_argument("--pace-usd-5h", type=float, help="never start a trial while the trailing 5 hours hold this many $")
    ap.add_argument("--arms", help="comma-separated arm names to limit token-recheck to (a later iteration)")
    ap.add_argument("--claude-week-start", type=float, help="plan 7-day utilization before the benchmark, 0-1 (from Claude Code's rate_limit_event)")
    a = ap.parse_args()

    if a.step == "collect":
        # jobs/pilot/<harness>/<step>/<job>/<trial>/result.json
        n = 0
        for d in sorted((ROOT / "jobs" / "pilot").glob("*/*")):
            n += write_csv(d, ROOT / "results" / "pilot" / f"{d.parent.name}-{d.name}.csv")
        print(f"{n} trials collected")
        return

    h = HARNESSES[a.harness]
    all_arms = arms_for(a.harness)
    if a.step == "token-check":
        arms = list(all_arms.values())
        trials = plan(["calibration/say-ok"], arms, a.harness, n=1, seed=SEED)
    elif a.step == "token-recheck":  # rescaled placebos only (METHOD.md 4.1)
        arms = [x for n, x in all_arms.items() if n.startswith("placebo-") and (not a.arms or n in a.arms.split(","))]
        trials = plan(["calibration/say-ok"], arms, a.harness, n=1, seed=SEED)
    elif a.step == "selection":
        arms = [all_arms["baseline"]]
        trials = plan(pool_tasks(), arms, a.harness, n=2 if a.harness == "claude-code" else 1, seed=SEED)
    elif a.step == "selection-extra":  # amendment 6: the added harder tasks, same baseline x2
        added = (ROOT / "tasks" / "pool" / "added-2026-09-29.txt").read_text().split()
        arms = [all_arms["baseline"]]
        trials = plan([f"pool/{t}" for t in added], arms, a.harness, n=2 if a.harness == "claude-code" else 1, seed=SEED)
    elif a.step == "third":  # section 6 rule 2 / 11.1: at most 5 third trials on 0/2 or 2/2 tasks, seeded order
        arms = [all_arms["baseline"]]
        trials = plan(third_trial_tasks(a.harness), arms, a.harness, n=1, seed=SEED)
    else:
        kill_tasks = [f"pool/{t}" for t in json.loads((ROOT / "tasks" / "pilot_plan.json").read_text())["kill_test_tasks"]]
        names = [f"skill-{s}" for s in KILL_SKILLS[a.harness]]
        names += sorted({f"placebo-{placebo_bucket_of(s, a.harness)}" for s in KILL_SKILLS[a.harness]})
        arms = [all_arms[n] for n in names]
        trials = plan(kill_tasks, arms, a.harness, n=2, seed=SEED)

    jobs_dir = ROOT / "jobs" / "pilot" / a.harness / a.step
    # The cap counts task trials only (METHOD.md amendment 5): calibration runs and infrastructure
    # retries are excluded; a trial is its base job, whatever its number of attempts.
    task_steps = ("selection", "selection-extra", "third", "kill")
    done_before = len({d.name.split("__r")[0] for st in task_steps
                       for d in (ROOT / "jobs" / "pilot" / a.harness / st).glob("b*__*") if d.is_dir()})
    planned_new = 0
    if a.step in task_steps:
        already = {d.name.split("__r")[0] for d in jobs_dir.glob("b*__*") if d.is_dir()} if jobs_dir.exists() else set()
        planned_new = len([t for t in trials if t.job_name not in already])
    if done_before + planned_new > PILOT_CAP[a.harness] and not a.dry_run:
        sys.exit(f"pilot cap: {done_before} task trials done + {planned_new} planned > {PILOT_CAP[a.harness]}")
    print(f"{a.harness} {a.step}: {len(trials)} trials, arms: {', '.join(x.name for x in arms)}")
    state = run_batch(trials, h, {x.name: x for x in arms}, jobs_dir, mounts=mounts(),
                      concurrency=a.concurrency, dry_run=a.dry_run,
                      units_budget=a.units_budget, window_start=a.window_start,
                      pace_units_5h=a.pace_units_5h, stop_after=a.stop_after,
                      codex_weekly_start=a.codex_weekly_start,
                      usd_budget=a.usd_budget, pace_usd_5h=a.pace_usd_5h,
                      claude_week_start=a.claude_week_start)
    if state.stopped:
        print(f"STOPPED: {state.stopped}")
        sys.exit(2)


if __name__ == "__main__":
    main()
