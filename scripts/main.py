#!/usr/bin/env python3
"""Main run (METHOD.md section 11.3 and amendment 9). One call per step; a stopped or interrupted
run resumes by calling the same step again (finished trials are adopted, not rerun).

  scripts/main.py claude-code [--stop-after N]   full design: 15 arms x 15 selected tasks x N=5
  scripts/main.py codex-topup                     after the Codex weekly reset: 3 skills + 2 placebos
  scripts/main.py collect                         jobs/main -> results/main/<harness>.csv
Add --dry-run to print the Harbor commands without running anything. The guards are fixed here, as
registered in amendment 9, not passed on the command line.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from skill_placebo.arms import NOT_ON_CODEX, PRIORITY, claude_arms, codex_arms, mounts, placebo_bucket_of  # noqa: E402
from skill_placebo.collect import write_csv  # noqa: E402
from skill_placebo.harnesses import HARNESSES  # noqa: E402
from skill_placebo.runner import plan, run_batch  # noqa: E402

SEED = 20260930  # amendment 9
N = 5
UNITS_PER_POINT = 5.8e6  # calibration: 1% of the Claude week ~ 5.8 M units
CLAUDE_GUARDS = dict(
    units_budget=25 * UNITS_PER_POINT,     # the benchmark's own ledger, per limit week: 25 points
    usd_budget=370.0,                      # second guard from amendment 3, per limit week
    window_start="2026-09-28T10:00:00Z",   # current limit week; then follows the reported reset
    rolling_week=True,
    pace_units_5h=75e6, pace_usd_5h=200.0,  # amendment 2 pace, unchanged
    claude_five_hour_pause=0.80,           # account 5-hour window: pause until its reset
    claude_week_cap=0.80, claude_week_cap_action="pause",  # account 7-day window: pause, not stop
    claude_week_relative_stop=False,       # the pilot's +25 points on the account window is replaced
)
DISK_GUARDS = dict(disk_pause_gib=10.0, disk_stop_gib=6.0)  # host volume, checked before each trial
CODEX_TOPUP_SKILLS = ["ponytail", "agent-skills", "compound-engineering"]
CODEX_TOPUP_TASKS = 10
CODEX_TOPUP_N = 4          # amendment 11: two batches of N=2, one per Codex weekly quota
CODEX_BATCH_BLOCKS = {1: (0, 1), 2: (2, 3)}


def selected_tasks() -> list[str]:
    return [f"pool/{t}" for t in json.loads((ROOT / "tasks" / "selected.json").read_text())["selected"]]


CODEX_MINIMAL_N = 3


def codex_floorless_tasks() -> list[str]:
    """The selected tasks in seeded order without those where Codex's baseline selection trial failed."""
    import pilot

    outcomes = pilot.selection_outcomes("codex")
    return [t for t in selected_tasks() if outcomes.get(t.split("/")[-1]) and all(outcomes[t.split("/")[-1]])]


def codex_topup_tasks() -> list[str]:
    """The selected tasks in their seeded order without those where Codex's baseline selection trial
    failed (the floor), first CODEX_TOPUP_TASKS of them (amendment 9)."""
    import pilot

    outcomes = pilot.selection_outcomes("codex")
    keep = [t for t in selected_tasks() if outcomes.get(t.split("/")[-1]) and all(outcomes[t.split("/")[-1]])]
    return keep[:CODEX_TOPUP_TASKS]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["claude-code", "codex-probe", "codex-topup", "codex-minimal", "collect"])
    ap.add_argument("--batch", type=int, choices=[1, 2], help="codex-topup: which batch of N=2 (amendment 11)")
    ap.add_argument("--weekly-start", type=float, help="codex-topup: Codex weekly used %% at the start of this quota (probe)")
    ap.add_argument("--concurrency", type=int, default=2)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--stop-after", type=int, help="stop after this many trials complete (report checkpoint)")
    a = ap.parse_args()

    if a.step == "collect":
        n = 0
        for d in sorted((ROOT / "jobs" / "main").glob("*")):
            if d.is_dir():
                n += write_csv(d, ROOT / "results" / "main" / f"{d.name}.csv")
        print(f"{n} trials collected")
        return

    if a.step == "codex-probe":  # one trivial Codex run: reads the weekly window and its reset time
        from skill_placebo.runner import codex_rate_limits, utc_iso
        import time as _time
        arms = [codex_arms(PRIORITY)["baseline"]]
        trials = plan(["calibration/say-ok"], arms, "codex", n=1, seed=SEED)
        jobs_dir = ROOT / "jobs" / "main" / f"codex-probe-{_time.strftime('%Y%m%dT%H%M%SZ', _time.gmtime())}"
        state = run_batch(trials, HARNESSES["codex"], {x.name: x for x in arms}, jobs_dir, mounts=mounts(),
                          concurrency=1, dry_run=a.dry_run, codex_pace_pct=40.0, codex_weekly_cap=80.0, **DISK_GUARDS)
        if not a.dry_run:
            rl = {}
            for d in sorted(jobs_dir.glob("b*__*")):
                rl.update(codex_rate_limits(d))
            print(f"PROBE codex weekly={rl.get('weekly')}% five_hour={rl.get('five_hour')}% "
                  f"weekly_resets_at={utc_iso(rl['weekly_resets_at']) if rl.get('weekly_resets_at') else None} "
                  f"stopped={state.stopped}")
        return

    if a.step == "codex-minimal":  # amendment 15: the pre-registered minimal design on Codex, final buckets
        harness, all_arms = "codex", codex_arms(PRIORITY)
        skills = [s for s in PRIORITY[:6] if s not in NOT_ON_CODEX]
        names = ["baseline"] + [f"skill-{s}" for s in skills]
        names += sorted({f"placebo-{placebo_bucket_of(s, harness)}" for s in skills})
        arms = [all_arms[n] for n in names]
        trials = plan(codex_floorless_tasks(), arms, harness, n=CODEX_MINIMAL_N, seed=SEED)
        jobs_dir = ROOT / "jobs" / "main" / harness
        print(f"codex minimal: {len(trials)} trials, {len(arms)} arms: {', '.join(x.name for x in arms)}")
        state = run_batch(trials, HARNESSES[harness], {x.name: x for x in arms}, jobs_dir, mounts=mounts(),
                          concurrency=a.concurrency, max_concurrency=3, dry_run=a.dry_run, stop_after=a.stop_after,
                          codex_pace_pct=90.0, codex_weekly_cap=95.0, codex_week_cap_action="pause",
                          codex_relative_stop=False, **DISK_GUARDS)
        if state.stopped:
            print(f"STOPPED: {state.stopped}")
            sys.exit(2)
        return

    if a.step == "claude-code":
        harness, all_arms = "claude-code", claude_arms(PRIORITY)
        arms = list(all_arms.values())
        trials = plan(selected_tasks(), arms, harness, n=N, seed=SEED)
        guards = CLAUDE_GUARDS
    else:
        harness, all_arms = "codex", codex_arms(PRIORITY)
        names = [f"skill-{s}" for s in CODEX_TOPUP_SKILLS]
        names += sorted({f"placebo-{placebo_bucket_of(s, harness)}" for s in CODEX_TOPUP_SKILLS})
        arms = [all_arms[n] for n in names]
        if not a.batch or a.weekly_start is None:
            sys.exit("codex-topup needs --batch 1|2 and --weekly-start (the probe's reading for this quota)")
        blocks = CODEX_BATCH_BLOCKS[a.batch]
        # Blocks 0-1 of the N=4 plan are the N=2 plan of amendment 9 (same seed, same shuffles).
        trials = [t for t in plan(codex_topup_tasks(), arms, harness, n=CODEX_TOPUP_N, seed=SEED) if t.block in blocks]
        guards = dict(codex_pace_pct=40.0, codex_weekly_cap=80.0, codex_weekly_start=a.weekly_start)

    jobs_dir = ROOT / "jobs" / "main" / harness
    print(f"{harness} main: {len(trials)} trials, {len(arms)} arms: {', '.join(x.name for x in arms)}")
    state = run_batch(trials, HARNESSES[harness], {x.name: x for x in arms}, jobs_dir, mounts=mounts(),
                      concurrency=a.concurrency if harness == "codex" else 2, dry_run=a.dry_run,
                      max_concurrency=3 if harness == "claude-code" else None,  # CONCURRENCY file, amendment 13
                      stop_after=a.stop_after, **guards, **DISK_GUARDS)
    if state.stopped:
        print(f"STOPPED: {state.stopped}")
        sys.exit(2)


if __name__ == "__main__":
    main()
