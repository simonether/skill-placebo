#!/usr/bin/env python3
"""Watchdog for METHOD.md amendment 15, point 3: Claude Code has priority over Codex.

While the Claude Code main run is going, every few minutes: the Docker VM must keep >= 1.5 GiB available,
the host >= 15 GiB free disk, and the median Claude Code trial wall time (normalized per task) after Codex
started must stay within x1.30 of its level before Codex (Claude Code trials since --cc-level-from). On the
first failure it writes <codex-jobs>/PAUSE (the Codex runner waits before its next trial) and leaves it
until the Claude Code run has finished. When the Claude Code batch is complete, it removes PAUSE and sets
Codex to concurrency 3, then exits.

  scripts/codex_watch.py --cc-jobs jobs/main/claude-code --codex-jobs jobs/main/codex \
      --cc-level-from 2026-09-30T02:31:07Z --codex-start <UTC>
"""
import argparse
import json
import os
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from load_watch import utc, vm_available_gib  # noqa: E402


def alive(jobs: Path) -> bool:
    try:
        os.kill(int((jobs / ".lock").read_text().strip()), 0)
        return True
    except (OSError, ValueError):
        return False


def cc_finished(jobs: Path) -> bool:
    try:
        state = json.loads((jobs / "batch-state.json").read_text())
        planned = len(json.loads((jobs / "plan.json").read_text()))
    except (OSError, json.JSONDecodeError):
        return False
    return not alive(jobs) and state.get("stopped") is None and len(state.get("done", [])) >= planned


def cc_ratio(jobs: Path, level_from: datetime, codex_start: datetime, min_after: int) -> tuple[float | None, int]:
    import statistics
    before: dict[str, list[float]] = {}
    after: list[tuple[str, float]] = []
    for res in jobs.glob("b*__*/*/result.json"):
        try:
            r = json.loads(res.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        if not (r.get("started_at") and r.get("finished_at") and r.get("task_name")):
            continue
        st = utc(r["started_at"])
        d = (utc(r["finished_at"]) - st).total_seconds()
        if level_from <= st < codex_start:
            before.setdefault(r["task_name"], []).append(d)
        elif st >= codex_start:
            after.append((r["task_name"], d))
    ratios = [d / statistics.median(before[t]) for t, d in after if before.get(t)]
    return (statistics.median(ratios) if len(ratios) >= min_after else None), len(ratios)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cc-jobs", default="jobs/main/claude-code")
    ap.add_argument("--codex-jobs", default="jobs/main/codex")
    ap.add_argument("--cc-level-from", required=True)
    ap.add_argument("--codex-start", required=True)
    ap.add_argument("--min-mem-gib", type=float, default=1.5)
    ap.add_argument("--min-disk-gib", type=float, default=15.0)
    ap.add_argument("--max-ratio", type=float, default=1.30)
    ap.add_argument("--min-after", type=int, default=12)
    ap.add_argument("--interval", type=int, default=300)
    a = ap.parse_args()
    cc, cx = Path(a.cc_jobs), Path(a.codex_jobs)
    level_from, codex_start = utc(a.cc_level_from), utc(a.codex_start)
    now = lambda: f"{datetime.now(timezone.utc):%H:%M:%SZ}"  # noqa: E731
    while True:
        if cc_finished(cc):
            (cx / "PAUSE").unlink(missing_ok=True)
            (cx / "CONCURRENCY").write_text("3\n")
            print(f"{now()} Claude Code run finished: Codex unpaused, concurrency 3", flush=True)
            return
        if not alive(cx) and (cx / "batch-state.json").exists():
            print(f"{now()} Codex runner not running; watch ends", flush=True)
            return
        paused = (cx / "PAUSE").exists()
        if alive(cc) and not paused:
            mem = vm_available_gib()
            disk = shutil.disk_usage("/").free / 2**30
            ratio, n = cc_ratio(cc, level_from, codex_start, a.min_after)
            why = None
            if mem is not None and mem < a.min_mem_gib:
                why = f"VM memory available {mem:.2f} GiB < {a.min_mem_gib}"
            elif disk < a.min_disk_gib:
                why = f"host disk free {disk:.1f} GiB < {a.min_disk_gib}"
            elif ratio is not None and ratio > a.max_ratio:
                why = f"Claude Code median normalized trial time x{ratio:.2f} > x{a.max_ratio} over {n} trials"
            print(f"{now()} check: mem={mem if mem is None else round(mem, 2)} GiB disk={disk:.0f} GiB "
                  f"cc_time_ratio={ratio if ratio is None else round(ratio, 2)} (n={n})", flush=True)
            if why:
                (cx / "PAUSE").write_text(f"codex_watch: {why}; until the Claude Code run ends (amendment 15)\n")
                print(f"{now()} PAUSE Codex: {why}", flush=True)
        time.sleep(a.interval)


if __name__ == "__main__":
    sys.exit(main())
