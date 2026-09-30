#!/usr/bin/env python3
"""Start the Codex main run (amendment 15) as soon as the Claude Code main run has finished.

Runs detached; checks every minute. "Finished" means the Claude Code batch completed (every planned trial
done, no stop reason, runner gone), not a checkpoint stop. Then it writes jobs/main/codex/CONCURRENCY = 3
and launches `scripts/main.py codex-minimal` in its own process session, logging to jobs/main-codex.log.
"""
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from codex_watch import cc_finished  # noqa: E402


def main():
    cc, cx = ROOT / "jobs" / "main" / "claude-code", ROOT / "jobs" / "main" / "codex"
    print(f"{datetime.now(timezone.utc):%H:%M:%SZ} waiting for the Claude Code main run to finish", flush=True)
    while not cc_finished(cc):
        time.sleep(60)
    cx.mkdir(parents=True, exist_ok=True)
    (cx / "CONCURRENCY").write_text("3\n")
    log = open(ROOT / "jobs" / "main-codex.log", "a")
    log.write(f"{datetime.now(timezone.utc):%Y-%m-%dT%H:%M:%SZ} Claude Code finished: Codex minimal design starts, concurrency 3\n")
    log.flush()
    p = subprocess.Popen(["caffeinate", "-i", "uv", "run", "python", "-u", "scripts/main.py", "codex-minimal",
                          "--concurrency", "3"], cwd=ROOT, stdout=log, stderr=subprocess.STDOUT,
                         stdin=subprocess.DEVNULL, start_new_session=True)
    print(f"{datetime.now(timezone.utc):%H:%M:%SZ} Codex runner started, pid {p.pid}", flush=True)


if __name__ == "__main__":
    main()
