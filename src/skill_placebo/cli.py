"""skill-placebo: rerun one skill's row of the benchmark (METHOD.md section 15).

  skill-placebo list                          the tested skills, their pinned commits and placebos
  skill-placebo run <owner/repo> [--n 2]      baseline, placebo and skill on the selected tasks, then R and pass

`run` needs Docker, uv and a Claude login for Claude Code (CLAUDE_CODE_OAUTH_TOKEN from `claude setup-token`,
or ANTHROPIC_API_KEY) in the environment. It spends real tokens: --max-usd stops it at a token-based $
estimate. Outside a checkout of the repository it clones the release into ~/.cache/skill-placebo/<version>
and runs there, because the tasks, placebos and runner live in the repository, not in the package.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

from . import __version__

REPO_URL = "https://github.com/simonether/skill-placebo"
HERE = Path(__file__).resolve().parents[2]


def is_checkout(root: Path) -> bool:
    return (root / "METHOD.md").exists() and (root / "tasks" / "selected.json").exists() and (root / "arms").is_dir()


def cached_checkout() -> Path:
    """The release's repository in the user cache, cloned once (tag v<version>, else main)."""
    dest = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "skill-placebo" / __version__
    if is_checkout(dest):
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    for ref in (f"v{__version__}", "main"):
        r = subprocess.run(["git", "clone", "--depth", "1", "--branch", ref, REPO_URL, str(dest)],
                           capture_output=True, text=True)
        if r.returncode == 0:
            return dest
    raise SystemExit(f"could not clone {REPO_URL} into {dest}")


def lock(root: Path) -> list[dict]:
    return json.loads((root / "skills.lock.json").read_text())["skills"]


def resolve_skill(root: Path, repo: str) -> dict:
    want = repo.lower().removeprefix("https://github.com/").strip("/")
    for s in lock(root):
        if want in (s["repo"].lower(), s["id"].lower()):
            return s
    names = ", ".join(s["repo"] for s in lock(root))
    raise SystemExit(f"{repo} is not one of the tested skills ({names}). A new skill needs its own placebo, "
                     "sized to its always-on text (METHOD.md 4.1); that is not automated yet.")


def cmd_list(root: Path) -> int:
    from .arms import placebo_bucket_of
    results = root / "results" / "main" / "claude-code.json"
    verdict = json.loads(results.read_text())["comparisons"] if results.exists() else {}
    for s in lock(root):
        v = verdict.get(s["id"], {})
        line = f"{s['repo']:40s} {s['sha'][:7]}  placebo {placebo_bucket_of(s['id'], 'claude-code')}"
        if v:
            line += f"  R {v['ratio']:.2f} [{v['ratio_ci'][0]:.2f}, {v['ratio_ci'][1]:.2f}]  {v['verdict']}"
        print(line)
    return 0


def claude_harness():
    """Claude Code as in the study, with whichever Claude login the environment provides."""
    from dataclasses import replace
    from .harnesses import CLAUDE_CODE
    if os.environ.get("CLAUDE_CODE_OAUTH_TOKEN"):
        return CLAUDE_CODE, {"CLAUDE_CODE_OAUTH_TOKEN": os.environ["CLAUDE_CODE_OAUTH_TOKEN"]}
    if os.environ.get("ANTHROPIC_API_KEY"):
        extra = {k: v for k, v in CLAUDE_CODE.extra_env.items() if k != "CLAUDE_FORCE_OAUTH"}
        return (replace(CLAUDE_CODE, creds=("ANTHROPIC_API_KEY",), extra_env=extra),
                {"ANTHROPIC_API_KEY": os.environ["ANTHROPIC_API_KEY"]})
    raise SystemExit("set CLAUDE_CODE_OAUTH_TOKEN (claude setup-token) or ANTHROPIC_API_KEY")


def summarize(jobs: Path, skill_id: str, placebo: str) -> None:
    from .analysis import compare
    from .collect import rows
    data: dict[str, dict[str, list]] = {}
    for r in rows(jobs):
        if r["passed"] is not None and r["cost_est_usd"] is not None:
            data.setdefault(r["arm"], {}).setdefault(r["task"], []).append((r["cost_est_usd"], bool(r["passed"])))
    for label, ctrl in (("placebo", f"placebo-{placebo}"), ("no skill", "baseline")):
        if f"skill-{skill_id}" in data and ctrl in data:
            c = compare(data[f"skill-{skill_id}"], data[ctrl])
            print(f"{skill_id} vs {label}: R = {c.ratio:.2f} [{c.ratio_ci[0]:.2f}, {c.ratio_ci[1]:.2f}], "
                  f"pass {c.pass_treat:.0%} vs {c.pass_control:.0%}, n = {c.n_treat}/{c.n_control} on {c.n_tasks} tasks")


def cmd_run(root: Path, a) -> int:
    from .arms import PRIORITY, claude_arms, mounts, placebo_bucket_of
    from .runner import plan, run_batch
    s = resolve_skill(root, a.repo)
    if not (root / "vendor" / s["id"]).is_dir():  # the skill at its pinned commit
        subprocess.run([sys.executable, str(root / "scripts" / "vendor_skills.py"), s["id"]], cwd=root, check=True)
    bucket = placebo_bucket_of(s["id"], "claude-code")
    all_arms = claude_arms(PRIORITY)
    arms = [all_arms["baseline"], all_arms[f"placebo-{bucket}"], all_arms[f"skill-{s['id']}"]]
    tasks = [f"pool/{t}" for t in json.loads((root / "tasks" / "selected.json").read_text())["selected"]]
    if a.tasks:
        keep = set(a.tasks.split(","))
        tasks = [t for t in tasks if t.split("/")[-1] in keep]
    trials = plan(tasks, arms, "claude-code", n=a.n, seed=a.seed)
    jobs = root / "jobs" / "cli" / f"{s['id']}-{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}"
    print(f"{s['repo']} @ {s['sha'][:7]}: {len(trials)} trials ({len(arms)} arms x {len(tasks)} tasks x N={a.n}), "
          f"placebo {bucket}, stop at ${a.max_usd:g} (token-based estimate) -> {jobs}")
    if a.dry_run:
        from .harnesses import CLAUDE_CODE
        run_batch(trials, CLAUDE_CODE, {x.name: x for x in arms}, jobs, mounts=mounts(), dry_run=True)
        import shutil
        shutil.rmtree(jobs, ignore_errors=True)  # a dry run leaves nothing behind
        return 0
    harness, creds = claude_harness()
    state = run_batch(trials, harness, {x.name: x for x in arms}, jobs, mounts=mounts(), concurrency=a.concurrency,
                      usd_budget=a.max_usd, disk_pause_gib=10.0, disk_stop_gib=6.0, secrets=creds)
    summarize(jobs, s["id"], bucket)
    if state.stopped:
        print(f"stopped: {state.stopped}")
        return 2
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="skill-placebo", description=__doc__.split("\n\n")[0])
    ap.add_argument("--version", action="version", version=__version__)
    sub = ap.add_subparsers(dest="cmd")
    sub.add_parser("list", help="the tested skills, their pinned commits and placebos")
    r = sub.add_parser("run", help="rerun one skill's row: baseline, placebo, skill on the selected tasks")
    r.add_argument("repo", help="owner/repo of a tested skill, e.g. DietrichGebert/ponytail")
    r.add_argument("--n", type=int, default=2, help="trials per task and arm (v1 used 2)")
    r.add_argument("--tasks", help="comma-separated task names, a subset of tasks/selected.json")
    r.add_argument("--concurrency", type=int, default=2)
    r.add_argument("--max-usd", type=float, default=50.0, help="stop at this token-based $ estimate")
    r.add_argument("--seed", type=int, default=20260930)
    r.add_argument("--dry-run", action="store_true", help="print the Harbor commands, run nothing")
    a = ap.parse_args(argv)
    if a.cmd is None:
        ap.print_help()
        return 0
    if not is_checkout(HERE):  # installed from PyPI: run inside the release's repository
        root = cached_checkout()
        return subprocess.run(["uv", "run", "--project", str(root), "skill-placebo", *(argv or sys.argv[1:])],
                              cwd=root).returncode
    return cmd_list(HERE) if a.cmd == "list" else cmd_run(HERE, a)


if __name__ == "__main__":
    sys.exit(main())
