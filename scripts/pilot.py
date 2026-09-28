#!/usr/bin/env python3
"""Pilot steps (METHOD.md section 11). One step per call, so each can be checked before the next.

  scripts/pilot.py token-check --harness claude-code   one trivial prompt per arm (section 4.1)
  scripts/pilot.py selection   --harness claude-code   pool tasks x 2 in the baseline arm (section 6)
  scripts/pilot.py selection   --harness codex         pool tasks x 1 in the baseline arm
  scripts/pilot.py kill        --harness claude-code   kill-test skills and their placebos (section 11)
  scripts/pilot.py collect                             jobs/pilot -> results/pilot/trials.csv
Add --dry-run to print the Harbor commands without running anything.
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
PILOT_CAP = {"claude-code": 150, "codex": 100}


def pool_tasks() -> list[str]:
    """Pool tasks that passed the oracle 2/2 (tasks/pool/ORACLE.md is the record)."""
    manifest = json.loads((ROOT / "tasks" / "pool" / "manifest.json").read_text())
    failed = set(json.loads((ROOT / "tasks" / "pool" / "oracle_failed.json").read_text())) \
        if (ROOT / "tasks" / "pool" / "oracle_failed.json").exists() else set()
    return [f"pool/{t['source']}/{t['name']}" for t in manifest["tasks"] if f"{t['source']}/{t['name']}" not in failed]


def arms_for(harness: str):
    return claude_arms(PRIORITY) if harness == "claude-code" else codex_arms(PRIORITY)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["token-check", "selection", "kill", "collect"])
    ap.add_argument("--harness", choices=list(HARNESSES), default="claude-code")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--concurrency", type=int, default=2)
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
    elif a.step == "selection":
        arms = [all_arms["baseline"]]
        trials = plan(pool_tasks(), arms, a.harness, n=2 if a.harness == "claude-code" else 1, seed=SEED)
    else:
        kill_tasks = [f"pool/{t}" for t in json.loads((ROOT / "tasks" / "pilot_plan.json").read_text())["kill_test_tasks"]]
        names = [f"skill-{s}" for s in KILL_SKILLS[a.harness]]
        names += sorted({f"placebo-{placebo_bucket_of(s, a.harness)}" for s in KILL_SKILLS[a.harness]})
        arms = [all_arms[n] for n in names]
        trials = plan(kill_tasks, arms, a.harness, n=2, seed=SEED)

    jobs_dir = ROOT / "jobs" / "pilot" / a.harness / a.step
    done_before = sum(1 for _ in (ROOT / "jobs" / "pilot" / a.harness).glob("*/*/*/result.json"))
    if done_before + len(trials) > PILOT_CAP[a.harness] and not a.dry_run:
        sys.exit(f"pilot cap: {done_before} done + {len(trials)} planned > {PILOT_CAP[a.harness]}")
    print(f"{a.harness} {a.step}: {len(trials)} trials, arms: {', '.join(x.name for x in arms)}")
    state = run_batch(trials, h, {x.name: x for x in arms}, jobs_dir, mounts=mounts(),
                      concurrency=a.concurrency, dry_run=a.dry_run)
    if state.stopped:
        print(f"STOPPED: {state.stopped}")
        sys.exit(2)


if __name__ == "__main__":
    main()
