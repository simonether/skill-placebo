#!/usr/bin/env python3
"""Amendment 9 applied to the pilot, retroactively: every pilot trial whose verifier timed out is
verified once more on its final state.

The pilot ran before snapshots existed and Harbor removed its containers, so the final state is
reconstructed: the task's image, plus the packages Claude Code's setup installs (they were in the
container the verifier ran in), plus the agent's shell commands replayed in order from its
session log. Only trials whose agent changed files through the Bash tool alone can be
reconstructed this way; any other tool that writes files makes the script refuse.

  scripts/pilot_verifier_rerun.py            # all pilot trials with VerifierTimeoutError
Writes <trial>/verifier_rerun.json (read by collect.trial_row) next to Harbor's own files.
"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from skill_placebo.runner import MAX_INFRA_RETRIES, rerun_result  # noqa: E402

# Claude Code's setup step in Harbor 0.23.0, as in every pilot trial.log.
SETUP_PACKAGES = "curl bash nodejs npm procps"
WRITING_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}


def agent_commands(trial: Path) -> list[str]:
    cmds = []
    for line in (trial / "agent" / "claude-code.txt").read_text(errors="replace").splitlines():
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        if ev.get("type") != "assistant":
            continue
        for c in ev["message"]["content"]:
            if c.get("type") != "tool_use":
                continue
            if c["name"] in WRITING_TOOLS:
                raise SystemExit(f"{trial}: the agent wrote files with {c['name']}; not reconstructible by replay")
            if c["name"] == "Bash":
                cmds.append(c["input"]["command"])
    return cmds


def task_dir_of(trial: Path) -> Path:
    name = json.loads((trial / "result.json").read_text())["task_name"]
    (hit,) = [p for p in (ROOT / "tasks" / "pool").glob(f"*/{name}") if (p / "task.toml").exists()]
    return hit


def main():
    env = {k: os.environ[k] for k in ("PATH", "HOME", "USER", "LANG", "TMPDIR") if k in os.environ}
    env["HARBOR_TELEMETRY"] = "0"
    for res in sorted((ROOT / "jobs" / "pilot").glob("*/*/*/*/result.json")):
        r = json.loads(res.read_text())
        if (r.get("exception_info") or {}).get("exception_type") != "VerifierTimeoutError":
            continue
        trial = res.parent
        if (trial / "verifier_rerun.json").exists():
            print(f"{trial.relative_to(ROOT)}: already done: {(trial / 'verifier_rerun.json').read_text()}")
            continue
        cmds = agent_commands(trial)
        src = task_dir_of(trial)
        base = trial.parent / "verifier-rerun"
        task = base / "task" / src.name
        if task.exists():
            shutil.rmtree(task)
        shutil.copytree(src, task)
        replay = task / "environment" / "sp-replay"
        replay.mkdir()
        lines = ["", "# skill-placebo amendment 9: reconstructed final state of the agent",
                 f"RUN apt-get update && apt-get install -y {SETUP_PACKAGES}", "COPY sp-replay /sp-replay"]
        for i, c in enumerate(cmds, 1):
            (replay / f"cmd-{i}.sh").write_text(c + "\n")
            lines.append(f"RUN cd /app 2>/dev/null; bash /sp-replay/cmd-{i}.sh > /sp-replay/cmd-{i}.out 2>&1; echo rc=$? >> /sp-replay/cmd-{i}.out")
        # /sp-replay stays in the image (outside /app) so the replay's own output can be checked.
        df = task / "environment" / "Dockerfile"
        df.write_text(df.read_text().rstrip("\n") + "\n" + "\n".join(lines) + "\n")
        rec = {"source": "reconstructed: task image + Claude Code setup packages + the agent's "
                         f"{len(cmds)} shell commands replayed in order (pilot, retroactive)",
               "attempts": []}
        for attempt in range(MAX_INFRA_RETRIES + 1):
            name = f"rerun-{attempt}"
            cmd = ["uv", "run", "--project", str(ROOT), "harbor", "run", "-p", str(task), "-a", "nop", "-k", "1",
                   "-n", "1", "-o", str(base), "--job-name", name, "--yes"]
            with open(base / f"{name}.runner.log", "w") as f:
                subprocess.run(cmd, cwd=ROOT, env=env, stdout=f, stderr=subprocess.STDOUT)
            out = rerun_result(base / name)
            rec["attempts"].append({"job": f"verifier-rerun/{name}", **out})
            if out["reward"] is not None or out["exception"] == "VerifierTimeoutError":
                break
        last = rec["attempts"][-1]
        if last["reward"] is not None:
            rec.update(outcome="rerun within timeout", reward=last["reward"])
        elif last["exception"] == "VerifierTimeoutError":
            rec["outcome"] = "timeout again"
        else:
            rec["outcome"] = f"rerun failed: {last['exception']}"
        (trial / "verifier_rerun.json").write_text(json.dumps(rec, indent=1) + "\n")
        print(f"{trial.relative_to(ROOT)}: {rec['outcome']}" + (f" reward={rec['reward']}" if "reward" in rec else ""))


if __name__ == "__main__":
    main()
