"""Trial runner on top of Harbor (METHOD.md sections 5, 7, 12).

One Harbor job per trial, so that the runner controls the order (randomized blocks, every arm
interleaved in time), the concurrency (at most 2 on subscriptions) and the stop rules (checked
after every trial). Harbor is launched with a clean environment: only PATH/HOME/locale, telemetry
off, and the credentials of the one harness being run. Nothing from the parent Claude Code session
(ANTHROPIC_BASE_URL, CLAUDE_CODE_*) reaches Harbor or the containers.
"""
from __future__ import annotations

import json
import os
import random
import re
import shlex
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field, asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SECRETS = ROOT / ".secrets" / "api.env"
HARBOR_VERSION = "0.23.0"  # pinned in pyproject.toml; custom agents in skill_placebo.harbor_agents need the same venv

# Markers of a usage limit or throttling in agent logs. Any hit stops the batch (METHOD.md 12).
LIMIT_MARKERS = re.compile(
    r"rate[_ ]limit(?:ed|_error|_event)|usage limit|limit reached|allowed_warning|"
    r"\b429\b|too many requests|quota|weekly limit|resets at",
    re.I,
)


@dataclass(frozen=True)
class Arm:
    name: str                      # baseline | placebo-<tier> | skill-<id>
    harbor_args: tuple[str, ...] = ()  # extra harbor flags (--skill, --ae ...)


@dataclass
class Harness:
    name: str                      # claude-code | codex
    agent: str                     # harbor agent name or module:Class
    model: str
    kwargs: dict = field(default_factory=dict)
    creds: tuple[str, ...] = ()    # names of variables taken from .secrets/api.env
    extra_env: dict = field(default_factory=dict)


@dataclass
class Trial:
    block: int
    order: int
    harness: str
    arm: str
    task: str

    @property
    def job_name(self) -> str:
        safe = re.sub(r"[^A-Za-z0-9_.-]", "_", self.task)
        return f"b{self.block:02d}-{self.order:04d}__{self.harness}__{self.arm}__{safe}"


def load_secrets() -> dict[str, str]:
    out = {}
    if SECRETS.exists():
        for line in SECRETS.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def clean_env(h: Harness, secrets: dict[str, str]) -> dict[str, str]:
    env = {k: os.environ[k] for k in ("PATH", "HOME", "USER", "LANG", "LC_ALL", "TMPDIR", "DOCKER_CONFIG", "DOCKER_HOST") if k in os.environ}
    env["HARBOR_TELEMETRY"] = "0"
    missing = [c for c in h.creds if c not in secrets]
    if missing:
        raise SystemExit(f"missing in .secrets/api.env: {', '.join(missing)}")
    for c in h.creds:
        env[c] = secrets[c]
    env.update(h.extra_env)
    return env


def plan(tasks: list[str], arms: list[Arm], harness: str, n: int, seed: int) -> list[Trial]:
    """n blocks; each block runs every (task, arm) once in a shuffled order."""
    rng = random.Random(seed)
    trials, order = [], 0
    for b in range(n):
        pairs = [(t, a.name) for t in tasks for a in arms]
        rng.shuffle(pairs)
        for t, a in pairs:
            trials.append(Trial(block=b, order=order, harness=harness, arm=a, task=t))
            order += 1
    return trials


def harbor_cmd(trial: Trial, h: Harness, arm: Arm, dataset: list[str], jobs_dir: Path, mounts: str | None) -> list[str]:
    cmd = ["uv", "run", "--project", str(ROOT), "harbor", "run", *dataset,
           "-i", trial.task, "-a", h.agent, "-m", h.model, "-k", "1", "-n", "1",
           "-o", str(jobs_dir), "--job-name", trial.job_name, "--yes"]
    for k, v in h.kwargs.items():
        cmd += ["--ak", f"{k}={json.dumps(v) if not isinstance(v, str) else v}"]
    if mounts:
        cmd += ["--mounts", mounts]
    cmd += list(arm.harbor_args)
    return cmd


def limit_hits(trial_dir: Path) -> list[str]:
    """Limit / throttling markers in a finished trial. Only harness-level events are scanned
    (Claude Code stream-json events other than assistant/user turns, Codex error and turn.failed
    events, Harbor's exception.txt), so a task that itself deals with HTTP 429 cannot trigger it."""
    hits = []

    def check(name, text):
        m = LIMIT_MARKERS.search(text)
        if m:
            hits.append(f"{name}: …{text[max(0, m.start() - 80): m.end() + 80]}…".replace("\n", " "))

    for p in trial_dir.rglob("exception.txt"):
        check(p.name, p.read_text(errors="replace"))
    for p in list(trial_dir.rglob("claude-code.txt")) + list(trial_dir.rglob("codex.txt")):
        for line in p.read_text(errors="replace").splitlines():
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(ev, dict):
                continue
            typ = str(ev.get("type", ""))
            if typ in ("assistant", "user") or typ.startswith("item."):
                continue
            if typ == "result" and not ev.get("is_error") and not ev.get("api_error_status"):
                continue
            check(p.name, line)
    return hits


def codex_weekly_percent(trial_dir: Path) -> float | None:
    """Highest weekly (secondary) used_percent seen in Codex rollout token_count events, if any."""
    best = None
    for p in trial_dir.rglob("rollout-*.jsonl"):
        for line in p.read_text(errors="replace").splitlines():
            if '"rate_limits"' not in line:
                continue
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            rl = (ev.get("payload") or {}).get("rate_limits") or ev.get("rate_limits") or {}
            sec = rl.get("secondary") or {}
            if isinstance(sec.get("used_percent"), (int, float)):
                best = max(best or 0.0, float(sec["used_percent"]))
    return best


@dataclass
class BatchState:
    done: list[str] = field(default_factory=list)
    stopped: str | None = None
    codex_weekly_start: float | None = None
    codex_weekly_last: float | None = None


def run_batch(trials: list[Trial], harness: Harness, arms: dict[str, Arm], dataset: list[str],
              jobs_dir: Path, mounts: str | None = None, concurrency: int = 2,
              weekly_budget_pp: float = 25.0, dry_run: bool = False) -> BatchState:
    jobs_dir.mkdir(parents=True, exist_ok=True)
    state_path = jobs_dir / "batch-state.json"
    state = BatchState(**json.loads(state_path.read_text())) if state_path.exists() else BatchState()
    (jobs_dir / "plan.json").write_text(json.dumps([asdict(t) for t in trials], indent=1))
    env = None if dry_run else clean_env(harness, load_secrets())
    todo = [t for t in trials if t.job_name not in state.done]

    def save():
        state_path.write_text(json.dumps(asdict(state), indent=1))

    def one(t: Trial):
        cmd = harbor_cmd(t, harness, arms[t.arm], dataset, jobs_dir, mounts)
        if dry_run:
            return t, 0, " ".join(shlex.quote(c) for c in cmd)
        log = jobs_dir / f"{t.job_name}.runner.log"
        with open(log, "w") as f:
            rc = subprocess.run(cmd, cwd=ROOT, env=env, stdout=f, stderr=subprocess.STDOUT).returncode
        return t, rc, str(log)

    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        pending = iter(todo)
        running = {}
        for _ in range(concurrency):
            t = next(pending, None)
            if t:
                running[pool.submit(one, t)] = t
        while running:
            fut = next(as_completed(running))
            t = running.pop(fut)
            t, rc, info = fut.result()
            if dry_run:
                print(info)
            else:
                tdir = jobs_dir / t.job_name
                hits = limit_hits(tdir)
                wk = codex_weekly_percent(tdir) if harness.name == "codex" else None
                if wk is not None:
                    if state.codex_weekly_start is None:
                        state.codex_weekly_start = wk
                    state.codex_weekly_last = wk
                state.done.append(t.job_name)
                print(f"{time.strftime('%H:%M:%S')} {t.job_name} rc={rc}" + (f" codex-weekly={wk}%" if wk is not None else ""))
                if hits:
                    state.stopped = "limit marker: " + hits[0][:300]
                elif wk is not None and state.codex_weekly_start is not None and wk - state.codex_weekly_start > weekly_budget_pp:
                    state.stopped = f"codex weekly usage +{wk - state.codex_weekly_start:.1f} pp > {weekly_budget_pp} pp"
                save()
                if state.stopped:
                    print(f"STOP: {state.stopped}")
                    for f in running:
                        f.cancel()
                    break
            t_next = next(pending, None)
            if t_next and not state.stopped:
                running[pool.submit(one, t_next)] = t_next
    save()
    return state
