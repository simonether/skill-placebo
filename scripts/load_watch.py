#!/usr/bin/env python3
"""Watchdog for METHOD.md amendment 13: while the batch runs at concurrency 3, check every few minutes
that (1) the Docker VM has >= 1.5 GiB memory available, (2) the host has >= 15 GiB free disk, (3) the
median trial wall time, normalized per task against trials before the switch, rose by <= 30%. On the
first failure it writes 2 into <jobs>/CONCURRENCY (the runner reads it when a slot frees) and exits.

  scripts/load_watch.py jobs/main/claude-code --switch-at 2026-09-30T02:30:00Z
Prints one line per check (and a final "REVERT"/"STOP" line) to stdout; run detached with a log file.
"""
import argparse
import json
import os
import shutil
import statistics
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


def utc(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def vm_available_gib() -> float | None:
    try:
        out = subprocess.run(["docker", "run", "--rm", "alpine:3", "free", "-m"], capture_output=True, text=True,
                             timeout=120).stdout
        for line in out.splitlines():
            if line.startswith("Mem:"):
                return int(line.split()[6]) / 1024
    except (subprocess.SubprocessError, OSError, ValueError, IndexError):
        return None
    return None


def normalized_ratio(jobs: Path, switch: datetime, min_after: int) -> tuple[float | None, int]:
    before: dict[str, list[float]] = {}
    after: list[tuple[str, float]] = []
    for res in jobs.glob("b*__*/*/result.json"):
        try:
            r = json.loads(res.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        if not (r.get("started_at") and r.get("finished_at") and r.get("task_name")):
            continue
        d = (utc(r["finished_at"]) - utc(r["started_at"])).total_seconds()
        (before.setdefault(r["task_name"], []).append(d) if utc(r["started_at"]) < switch
         else after.append((r["task_name"], d)))
    ratios = [d / statistics.median(before[t]) for t, d in after if before.get(t)]
    if len(ratios) < min_after:
        return None, len(ratios)
    return statistics.median(ratios), len(ratios)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("jobs")
    ap.add_argument("--switch-at", required=True, help="UTC time the batch went to concurrency 3")
    ap.add_argument("--min-mem-gib", type=float, default=1.5)
    ap.add_argument("--min-disk-gib", type=float, default=15.0)
    ap.add_argument("--max-ratio", type=float, default=1.30)
    ap.add_argument("--min-after", type=int, default=12, help="trials after the switch before the time check applies")
    ap.add_argument("--interval", type=int, default=300)
    a = ap.parse_args()
    jobs, switch = Path(a.jobs), utc(a.switch_at)
    conc = jobs / "CONCURRENCY"
    while True:
        lock = jobs / ".lock"
        try:
            os.kill(int(lock.read_text().strip()), 0)
        except (OSError, ValueError):
            print(f"{datetime.now(timezone.utc):%H:%M:%SZ} STOP: runner not running", flush=True)
            return
        if conc.exists() and conc.read_text().strip() == "3":
            mem = vm_available_gib()
            disk = shutil.disk_usage("/").free / 2**30
            ratio, n = normalized_ratio(jobs, switch, a.min_after)
            why = None
            if mem is not None and mem < a.min_mem_gib:
                why = f"VM memory available {mem:.2f} GiB < {a.min_mem_gib}"
            elif disk < a.min_disk_gib:
                why = f"host disk free {disk:.1f} GiB < {a.min_disk_gib}"
            elif ratio is not None and ratio > a.max_ratio:
                why = f"median normalized trial time x{ratio:.2f} > x{a.max_ratio} over {n} trials"
            print(f"{datetime.now(timezone.utc):%H:%M:%SZ} check: mem={mem if mem is None else round(mem, 2)} GiB "
                  f"disk={disk:.0f} GiB time_ratio={ratio if ratio is None else round(ratio, 2)} (n={n})", flush=True)
            if why:
                conc.write_text("2\n")
                print(f"{datetime.now(timezone.utc):%H:%M:%SZ} REVERT to 2: {why}", flush=True)
                return
        time.sleep(a.interval)


if __name__ == "__main__":
    sys.exit(main())
