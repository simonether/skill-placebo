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
    r"\b429\b|too many requests|quota|weekly limit|resets at|"
    # Authentication failures also stop the batch: every later trial would fail the same way.
    r"authentication_failed|not logged in|invalid[_ ]api[_ ]key|oauth token has expired|\b401\b",
    re.I,
)


DOCKER_LIMIT = re.compile(r"toomanyrequests|registry[^\n]{0,200}429 Too Many Requests|pull rate limit", re.I)


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
        safe = re.sub(r"[^A-Za-z0-9_.-]", "_", self.task.split("/")[-1])
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


INFRA_EXCEPTIONS = {"AgentSetupTimeoutError", "EnvironmentStartTimeoutError", "HealthcheckError", "SandboxBuildFailedError"}
MAX_INFRA_RETRIES = 2


def infra_failure(job_dir: Path) -> str | None:
    """The exception type if the trial failed for infrastructure reasons (METHOD.md section 7):
    the agent never got to work, so the trial is rerun. VerifierTimeoutError is not infra: the
    agent's own code can hang the tests."""
    for res in job_dir.glob("*/result.json"):
        try:
            info = json.loads(res.read_text()).get("exception_info") or {}
        except (OSError, json.JSONDecodeError):
            continue
        typ, msg = info.get("exception_type"), str(info.get("exception_message") or "")
        if typ in INFRA_EXCEPTIONS or (typ == "RuntimeError" and "docker" in msg.lower()):
            return typ
    return None


def running_batches(exclude: Path | None = None) -> list[Path]:
    """Batch directories whose runner process is alive (their .lock holds a live pid)."""
    live = []
    for lock in (ROOT / "jobs").rglob(".lock"):
        if exclude is not None and lock.parent == exclude:
            continue
        try:
            os.kill(int(lock.read_text().strip()), 0)
            live.append(lock.parent)
        except (ProcessLookupError, ValueError, OSError):
            pass
    return live


def assert_frozen_ok(what: str) -> None:
    """arms/ and vendor/ are frozen while any trial runs (after a rebuild during a run, 2026-09-29)."""
    live = running_batches()
    if live:
        raise SystemExit(f"{what}: refused, arms/ and vendor/ are frozen while batches run: {', '.join(str(p) for p in live)}")


def arm_host_dirs(arm: Arm, mounts: str | None) -> list[Path]:
    """Host directories whose content defines the arm: its plugin, memory file, marketplace and the
    plugin that marketplace installs, or its --skill directories."""
    targets = {m["target"]: Path(m["source"]) for m in (json.loads(mounts) if mounts else [])}
    args, dirs = list(arm.harbor_args), []
    for i, a in enumerate(args):
        nxt = args[i + 1] if i + 1 < len(args) else ""
        if a == "--skill":
            dirs.append(Path(nxt))
        elif a == "--ae" and "=" in nxt:
            k, v = nxt.split("=", 1)
            paths = []
            if k in ("CLAUDE_CODE_PLUGIN_DIRS", "SP_CODEX_MARKETPLACES"):
                paths = v.split(":")
            elif k == "SP_CLAUDE_MD":
                paths = [str(Path(v).parent)]
            for c in paths:
                if c in targets:
                    dirs.append(targets[c])
                    name = Path(c).name
                    if name.startswith("mkt-") and f"/opt/plugins/{name[4:]}" in targets:
                        dirs.append(targets[f"/opt/plugins/{name[4:]}"])
    return dirs


def tree_hash(dirs: list[Path]) -> str | None:
    """sha256 over relative paths and file contents (without .git); None when there is nothing to hash."""
    import hashlib

    if not dirs:
        return None
    h = hashlib.sha256()
    for d in dirs:
        files = sorted(p for p in Path(d).rglob("*") if p.is_file() and ".git" not in p.relative_to(d).parts)
        h.update(f"#{len(files)}".encode())
        for f in files:
            h.update(str(f.relative_to(d)).encode())
            h.update(f.read_bytes())
    return h.hexdigest()


def arm_not_applied(job_dir: Path, arm: Arm) -> str | None:
    """Manipulation check: the arm's plugin or memory file actually reached the agent. A trial where
    it did not is an infrastructure failure, not data (e.g. a placebo directory rebuilt while a
    container was running, or a Codex plugin install that failed during setup)."""
    args = list(arm.harbor_args)
    env = {}
    for i, a in enumerate(args):
        if a == "--ae" and i + 1 < len(args) and "=" in args[i + 1]:
            k, v = args[i + 1].split("=", 1)
            env[k] = v
    for tdir in job_dir.glob("*/"):
        if not (tdir / "result.json").exists():
            continue
        if "CLAUDE_CODE_PLUGIN_DIRS" in env:
            want = env["CLAUDE_CODE_PLUGIN_DIRS"]
            loaded = []
            for p in tdir.rglob("claude-code.txt"):
                for line in p.read_text(errors="replace").splitlines():
                    if '"subtype":"init"' in line or '"subtype": "init"' in line:
                        try:
                            loaded = [x.get("path") for x in json.loads(line).get("plugins") or []]
                        except json.JSONDecodeError:
                            pass
                        break
            if want not in loaded:
                return f"plugin {want} not loaded (init plugins: {loaded})"
        if "SP_CLAUDE_MD" in env and not (tdir / "agent" / "sessions" / "CLAUDE.md").exists():
            return "user CLAUDE.md not installed"
        if "SP_CODEX_PLUGINS" in env:
            info = json.loads((tdir / "result.json").read_text()).get("exception_info") or {}
            msg = str(info.get("exception_message") or "")
            if info.get("exception_type") == "NonZeroAgentExitCodeError" and ("codex plugin" in msg or "marketplace" in msg):
                return "codex plugin install failed during setup"
    return None


def harbor_cmd(trial: Trial, h: Harness, arm: Arm, jobs_dir: Path, mounts: str | None, job_name: str | None = None,
               snapshot: bool = False) -> list[str]:
    """trial.task is a task directory relative to tasks/ (e.g. pool/swebench-verified/django__django-15957).
    snapshot: launch through skill_placebo.harbor_launch, which commits the agent's final container
    state before the verifier starts (METHOD.md amendment 9)."""
    launcher = ["python", "-m", "skill_placebo.harbor_launch"] if snapshot else ["harbor"]
    cmd = ["uv", "run", "--project", str(ROOT), *launcher, "run", "-p", str(ROOT / "tasks" / trial.task),
           "-a", h.agent, "-m", h.model, "-k", "1", "-n", "1",
           "-o", str(jobs_dir), "--job-name", job_name or trial.job_name, "--yes",
           # Agent install (apt/npm) is not the agent's work; slow mirrors must not fail trials.
           "--agent-setup-timeout-multiplier", "2"]
    for k, v in h.kwargs.items():
        cmd += ["--ak", f"{k}={json.dumps(v) if not isinstance(v, str) else v}"]
    if mounts:
        cmd += ["--mounts", mounts]
    cmd += list(arm.harbor_args)
    return cmd


def _docker(*args: str, timeout: float = 300) -> subprocess.CompletedProcess:
    return subprocess.run(["docker", *args], capture_output=True, text=True, timeout=timeout)


def record_interrupted(job_dir: Path, harness: str, model: str) -> dict | None:
    """An attempt without result.json and without a live Harbor process was interrupted (runner or
    host stopped). Record it once: <job>/interrupted.json and a ledger row with the tokens it used,
    flagged as an infrastructure failure; the trial itself is retried (METHOD.md section 7)."""
    from .collect import cost_from_tokens, partial_usage, units_from_tokens

    if (job_dir / "interrupted.json").exists() or list(job_dir.glob("*/result.json")):
        return None
    if subprocess.run(["pgrep", "-f", "--", f"--job-name {re.escape(job_dir.name)}( |$)"],
                      capture_output=True).returncode == 0:
        return None  # still running (e.g. a trial finishing while its runner is replaced)
    trial_dirs = [d for d in job_dir.glob("*/") if (d / "config.json").exists()]
    u = partial_usage(job_dir)
    rec = {"reason": "interrupted: no result.json and no live Harbor process (runner or host stopped)",
           "phase": "verification" if any((d / "snapshot.json").exists() for d in trial_dirs) else "agent or setup",
           "tokens_from": "partial Claude Code stream", **u}
    (job_dir / "interrupted.json").write_text(json.dumps(rec, indent=1) + "\n")
    mm = re.search(r"__r(\d+)$", job_dir.name)
    row = {"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "job": job_dir.name,
           "trial": trial_dirs[0].name if trial_dirs else None, "arm": job_dir.name.split("__")[2],
           "model": model.split("/")[-1], "exception": "Interrupted", "attempt": int(mm.group(1)) if mm else 0,
           "infra_failure": 1, "n_input": u["n_input"], "n_cached": u["n_cached"],
           "n_cache_write": u["n_cache_write"], "n_output": u["n_output"],
           "cost_est_usd": cost_from_tokens(model, u["n_input"], u["n_cached"], u["n_cache_write"], u["n_output"]),
           "units": units_from_tokens(u["n_input"], u["n_cached"], u["n_cache_write"], u["n_output"]),
           "arm_hash": None, "verifier_rerun": None, "passed": None, "plan_five_hour": None, "plan_week": None}
    with open(ledger_path(harness), "a") as f:
        f.write(json.dumps(row) + "\n")
    return rec


def units_from_partial(u: dict) -> float:
    from .collect import units_from_tokens

    return units_from_tokens(u["n_input"], u["n_cached"], u["n_cache_write"], u["n_output"])


def remove_snapshots(job_dir: Path) -> None:
    """Delete the snapshot images of a finished attempt (they are only needed for a rerun)."""
    for snap in job_dir.glob("*/snapshot.json"):
        try:
            tag = json.loads(snap.read_text()).get("image")
        except (OSError, json.JSONDecodeError):
            continue
        if tag:
            _docker("rmi", "-f", tag)


def host_free_gib(path: str = "/") -> float:
    """Free space on the host volume that holds Docker Desktop's disk, as `df` reports it."""
    import shutil

    return shutil.disk_usage(path).free / 2**30


def disk_state(free_gib: float, pause_gib: float | None, stop_gib: float | None) -> str:
    """'stop' below stop_gib, 'pause' below pause_gib, else 'go'."""
    if stop_gib is not None and free_gib < stop_gib:
        return "stop"
    if pause_gib is not None and free_gib < pause_gib:
        return "pause"
    return "go"


def sweep_snapshots(own: Path | None = None) -> None:
    """Remove snapshot images left by an interrupted run; only when no other batch is running."""
    from .harbor_launch import SNAPSHOT_REPO

    if running_batches(exclude=own):
        return
    out = _docker("images", "-q", SNAPSHOT_REPO).stdout.split()
    if out:
        _docker("rmi", "-f", *sorted(set(out)))


def derived_task(task_dir: Path, image: str, out: Path) -> Path:
    """A copy of the task whose environment is the given local image (the verifier and its timeout
    are the task's own)."""
    import shutil

    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(task_dir, out)
    toml = out / "task.toml"
    lines = [ln for ln in toml.read_text().splitlines() if not ln.strip().startswith("docker_image")]
    idx = next(i for i, ln in enumerate(lines) if ln.strip() == "[environment]")
    lines.insert(idx + 1, f'docker_image = "{image}"')
    toml.write_text("\n".join(lines) + "\n")
    return out


def rerun_result(rerun_job: Path) -> dict:
    """Reward and exception of a rerun job: {'reward': float|None, 'exception': str|None}."""
    for res in rerun_job.glob("*/result.json"):
        try:
            r = json.loads(res.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        if not r.get("task_name"):
            continue
        rw = ((r.get("verifier_result") or {}).get("rewards") or {}).get("reward")
        return {"reward": None if rw is None else float(rw), "exception": (r.get("exception_info") or {}).get("exception_type")}
    return {"reward": None, "exception": "no result"}


def verifier_rerun(job_dir: Path, task_dir: Path, env: dict | None) -> list[dict]:
    """METHOD.md amendment 9: a trial whose verifier timed out is verified once more, on the image
    committed before its first verification, with the same verifier and timeout and no agent.
    Within the timeout, its reward is the trial's result and the episode is flagged as
    infrastructure; another timeout (or no snapshot) leaves a failed trial. A rerun that itself
    fails on infrastructure is repeated up to MAX_INFRA_RETRIES times. Writes
    <trial>/verifier_rerun.json, which collect.trial_row reads."""
    out = []
    for tdir in sorted(job_dir.glob("*/")):
        res = tdir / "result.json"
        if not res.exists() or (tdir / "verifier_rerun.json").exists():
            continue
        info = json.loads(res.read_text()).get("exception_info") or {}
        if info.get("exception_type") != "VerifierTimeoutError":
            continue
        snap = {}
        if (tdir / "snapshot.json").exists():
            snap = json.loads((tdir / "snapshot.json").read_text())
        rec = {"source": "snapshot before the first verification", "snapshot": snap.get("image"),
               "snapshot_error": snap.get("error"), "attempts": []}
        if not snap.get("image"):
            rec["outcome"] = "no snapshot"
        else:
            base = job_dir / "verifier-rerun"
            task = derived_task(task_dir, snap["image"], base / "task" / task_dir.name)
            for attempt in range(MAX_INFRA_RETRIES + 1):
                name = f"rerun-{attempt}"
                cmd = ["uv", "run", "--project", str(ROOT), "harbor", "run", "-p", str(task), "-a", "nop",
                       "-k", "1", "-n", "1", "-o", str(base), "--job-name", name, "--yes"]
                with open(base / f"{name}.runner.log", "w") as f:
                    subprocess.run(cmd, cwd=ROOT, env=env, stdout=f, stderr=subprocess.STDOUT)
                r = rerun_result(base / name)
                rec["attempts"].append({"job": f"verifier-rerun/{name}", **r})
                if r["reward"] is not None or r["exception"] == "VerifierTimeoutError":
                    break
            last = rec["attempts"][-1]
            if last["reward"] is not None:
                rec.update(outcome="rerun within timeout", reward=last["reward"])
            elif last["exception"] == "VerifierTimeoutError":
                rec["outcome"] = "timeout again"
            else:
                rec["outcome"] = f"rerun failed: {last['exception']}"
        (tdir / "verifier_rerun.json").write_text(json.dumps(rec, indent=1) + "\n")
        out.append(rec)
    return out


def limit_hits(trial_dir: Path) -> list[str]:
    """Limit, throttling and auth-failure markers in a finished trial. Only events that report a
    harness error are scanned (errored results, error/retry/limit system events without hook output,
    non-"allowed" rate_limit_events, Codex error and turn.failed), so neither a task nor a plugin's
    text that mentions HTTP 401/429 can trigger a stop."""
    hits = []

    def check(name, text):
        m = LIMIT_MARKERS.search(text)
        if m:
            hits.append(f"{name}: …{text[max(0, m.start() - 80): m.end() + 80]}…".replace("\n", " "))

    # exception.txt embeds the full agent command, task instruction included, so only Docker
    # registry throttling is looked for there; model-side limits come from structured events.
    for p in trial_dir.rglob("exception.txt"):
        text = p.read_text(errors="replace")
        m = DOCKER_LIMIT.search(text)
        if m:
            hits.append(f"{p.name}: …{text[max(0, m.start() - 80): m.end() + 80]}…".replace("\n", " "))
    for p in list(trial_dir.rglob("claude-code.txt")) + list(trial_dir.rglob("codex.txt")):
        for line in p.read_text(errors="replace").splitlines():
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(ev, dict):
                continue
            typ = str(ev.get("type", ""))
            if typ == "rate_limit_event":
                # Claude Code reports the plan's windows on every run; only a non-"allowed" status or
                # overage use is a limit signal.
                info = ev.get("rate_limit_info") or {}
                if info.get("status") != "allowed" or info.get("isUsingOverage"):
                    hits.append(f"{p.name}: rate_limit_event status={info.get('status')} overage={info.get('isUsingOverage')}")
            elif typ == "result":
                # Only an errored result carries harness-level text (e.g. "Not logged in", "API Error: 429").
                if ev.get("is_error") or ev.get("api_error_status"):
                    check(p.name, f"{ev.get('api_error_status')} {ev.get('result')}")
            elif typ == "system":
                # Informational system events (init, hook_started/hook_response with a plugin's text)
                # never count; only error/retry/limit subtypes, without any hook output.
                sub = str(ev.get("subtype", ""))
                if re.search(r"error|retry|limit|fail", sub, re.I):
                    check(p.name, json.dumps({k: v for k, v in ev.items() if k not in ("output", "stdout", "stderr")}))
            elif typ in ("error", "turn.failed"):  # Codex
                check(p.name, json.dumps(ev))
    return hits


def codex_rate_limits(trial_dir: Path) -> dict:
    """Last Codex rate-limit reading in a trial's rollout: {'weekly': %, 'five_hour': %, 'five_hour_resets_s': s}."""
    out = {}
    for p in trial_dir.rglob("rollout-*.jsonl"):
        for line in p.read_text(errors="replace").splitlines():
            if '"rate_limits"' not in line:
                continue
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            rl = (ev.get("payload") or {}).get("rate_limits") or ev.get("rate_limits") or {}
            prim, sec = rl.get("primary") or {}, rl.get("secondary") or {}
            if isinstance(sec.get("used_percent"), (int, float)):
                out["weekly"] = float(sec["used_percent"])
            if isinstance(prim.get("used_percent"), (int, float)):
                out["five_hour"] = float(prim["used_percent"])
                for k in ("resets_in_seconds", "resets_after_seconds"):
                    if isinstance(prim.get(k), (int, float)):
                        out["five_hour_resets_s"] = float(prim[k])
    return out


def claude_windows(trial_dir: Path) -> dict:
    """Last plan-window utilization Claude Code reported in a trial (account-wide, as on the usage
    page): {'five_hour': 0.13, 'seven_day': 0.04, 'seven_day_resets': epoch}."""
    out = {}
    for p in trial_dir.rglob("claude-code.txt"):
        for line in p.read_text(errors="replace").splitlines():
            if '"rate_limit_event"' not in line:
                continue
            try:
                info = json.loads(line).get("rate_limit_info") or {}
            except json.JSONDecodeError:
                continue
            w = info.get("unifiedWindows") or {}
            for k in ("five_hour", "seven_day"):
                if isinstance((w.get(k) or {}).get("utilization"), (int, float)):
                    out[k] = float(w[k]["utilization"])
            if (w.get("seven_day") or {}).get("resetsAt"):
                out["seven_day_resets"] = w["seven_day"]["resetsAt"]
            if (w.get("five_hour") or {}).get("resetsAt"):
                out["five_hour_resets"] = w["five_hour"]["resetsAt"]
    return out


def codex_weekly_percent(trial_dir: Path) -> float | None:
    return codex_rate_limits(trial_dir).get("weekly")


@dataclass
class BatchState:
    done: list[str] = field(default_factory=list)
    stopped: str | None = None
    codex_weekly_start: float | None = None
    codex_weekly_last: float | None = None
    usd_spent_window: float = 0.0


def ledger_path(harness: str) -> Path:
    """Every trial of the benchmark on one harness, with its token-based $ equivalent (METHOD.md
    amendment 1). The stop rule sums this ledger, across batches, from the window start."""
    return ROOT / "jobs" / f"ledger-{harness}.jsonl"


def ledger_spent(harness: str, window_start: str | None, field_name: str = "units") -> float:
    """Sum of `field_name` over ledger rows with ts >= window_start (UTC ISO 'YYYY-MM-DDTHH:MM:SSZ')."""
    p = ledger_path(harness)
    if not p.exists():
        return 0.0
    total = 0.0
    for line in p.read_text().splitlines():
        row = json.loads(line)
        if window_start is None or row["ts"] >= window_start:
            total += row.get(field_name) or 0.0
    return total


def msk_now() -> str:
    """Wall clock for runner output in Moscow time (UTC+3), whatever the machine's zone (UTC+5)."""
    return time.strftime("%H:%M:%S", time.gmtime(time.time() + 3 * 3600)) + " MSK"


def utc_iso(t: float) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t))


def pace_wait_seconds(harness: str, pace_units: float, window_s: int = 5 * 3600, now: float | None = None,
                      field_name: str = "units") -> float:
    """Seconds to wait until `field_name` logged in the trailing window drops below pace_units (0 = go)."""
    now = time.time() if now is None else now
    p = ledger_path(harness)
    if not p.exists():
        return 0.0
    rows = []
    for line in p.read_text().splitlines():
        r = json.loads(line)
        t = time.mktime(time.strptime(r["ts"], "%Y-%m-%dT%H:%M:%SZ")) - time.timezone
        if t >= now - window_s:
            rows.append((t, r.get(field_name) or 0.0))
    total = sum(u for _, u in rows)
    if total < pace_units:
        return 0.0
    rows.sort()
    for t, u in rows:  # drop the oldest entries until under the pace
        total -= u
        if total < pace_units:
            return max(0.0, t + window_s - now)
    return float(window_s)


def ledger_add(harness: str, trial_dir: Path, arm_hash: str | None = None) -> float:
    """Append every trial found under trial_dir's job to the ledger; returns their units."""
    from .collect import trial_row  # local import: collect imports nothing from runner

    added = 0.0
    windows = claude_windows(trial_dir) if harness == "claude-code" else {}
    rl = codex_rate_limits(trial_dir) if harness == "codex" else {}
    with open(ledger_path(harness), "a") as f:
        for res in sorted(trial_dir.glob("*/result.json")):
            row = trial_row(res)
            if not row:
                continue
            rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "job": trial_dir.name, "trial": row["trial"],
                   "arm": row["arm"], "model": row["model"], "exception": row["exception"],
                   "attempt": row["attempt"], "infra_failure": row["infra_failure"],
                   "n_input": row["n_input"], "n_cached": row["n_cached"], "n_cache_write": row["n_cache_write"],
                   "n_output": row["n_output"], "cost_est_usd": row["cost_est_usd"], "units": row["units"],
                   "arm_hash": arm_hash, "verifier_rerun": row["verifier_rerun"], "passed": row["passed"],
                   "plan_five_hour": windows.get("five_hour", rl.get("five_hour")),
                   "plan_week": windows.get("seven_day", rl.get("weekly"))}
            f.write(json.dumps(rec) + "\n")
            added += row["units"] or 0.0
    return added


def run_batch(trials: list[Trial], harness: Harness, arms: dict[str, Arm],
              jobs_dir: Path, mounts: str | None = None, concurrency: int = 2,
              weekly_budget_pp: float = 25.0, dry_run: bool = False,
              units_budget: float | None = None, window_start: str | None = None,
              pace_units_5h: float | None = None, stop_after: int | None = None,
              codex_weekly_start: float | None = None, codex_pace_pct: float = 40.0,
              codex_weekly_cap: float = 80.0,
              usd_budget: float | None = None, pace_usd_5h: float | None = None,
              claude_week_start: float | None = None, claude_five_hour_pause: float = 0.80,
              claude_week_cap: float = 0.80, claude_week_cap_action: str = "stop",
              claude_week_relative_stop: bool = True, rolling_week: bool = False,
              week_pause_probe_s: int = 3600, disk_pause_gib: float | None = None,
              disk_stop_gib: float | None = None, disk_check_s: int = 60) -> BatchState:
    """units_budget: stop once the ledger's limit units since window_start (the plan's weekly reset,
    UTC) reach it - the translation of 25% of the week (METHOD.md amendment 2). Required for
    real runs. pace_units_5h: never start a trial while the trailing 5 hours hold that many units.
    stop_after: stop after that many trials complete in this call (checkpoints).
    codex_weekly_start: the plan's weekly used % before the benchmark; the batch stops at
    +weekly_budget_pp or at codex_weekly_cap absolute. codex_pace_pct: pause while Codex's 5-hour
    window is this full. usd_budget / pace_usd_5h: the same stop and pace in the token-based $
    equivalent (2026-09-29); when both units and $ limits are given, whichever binds first.
    claude_week_start: the plan's 7-day utilization (0-1) before the benchmark; the batch stops at
    +weekly_budget_pp of it (account-wide, so conservative) unless claude_week_relative_stop is
    False. claude_five_hour_pause: pause while the account's 5-hour window is this full, to leave
    the owner room. claude_week_cap_action: "stop" or "pause" when the account's 7-day window
    reaches claude_week_cap; a pause lasts until the weekly reset or week_pause_probe_s, whichever
    comes first, and the next trial reads the window again (main run, METHOD.md amendment 9).
    rolling_week: window_start follows the plan's weekly reset reported by Claude Code, so the
    ledger budget applies per limit week. Every trial whose verifier times out is verified once
    more on its snapshot (amendment 9). disk_pause_gib / disk_stop_gib: before each trial starts,
    pause while the host volume has less free space than the first, stop below the second (Docker
    Desktop's disk can share the host volume with other projects)."""
    jobs_dir.mkdir(parents=True, exist_ok=True)
    lock = jobs_dir / ".lock"
    if not dry_run:
        # One process per batch: resuming while a stopped run still waits for in-flight trials
        # would start those trials a second time (happened once in the 29.09 calibration).
        if lock.exists():
            try:
                os.kill(int(lock.read_text().strip()), 0)
                raise SystemExit(f"batch {jobs_dir} is still running (pid {lock.read_text().strip()})")
            except (ProcessLookupError, ValueError):
                pass
        lock.write_text(str(os.getpid()))
    state_path = jobs_dir / "batch-state.json"
    state = BatchState(**json.loads(state_path.read_text())) if state_path.exists() else BatchState()
    (jobs_dir / "plan.json").write_text(json.dumps([asdict(t) for t in trials], indent=1))
    unresolved = [k for k, v in harness.kwargs.items() if "TBD" in json.dumps(v)]
    if unresolved and not dry_run:
        raise SystemExit(f"{harness.name}: unresolved placeholders in {', '.join(unresolved)}")
    if not dry_run and units_budget is None and usd_budget is None and harness.name != "codex":
        raise SystemExit("units_budget or usd_budget is required for real runs (METHOD.md amendments 1-2)")
    units_budget = float("inf") if units_budget is None else units_budget
    usd_budget = float("inf") if usd_budget is None else usd_budget
    env = None if dry_run else clean_env(harness, load_secrets())
    if not dry_run:
        for t in trials:  # a trial that finished after a stop was recorded: adopt it, don't rerun
            if t.job_name not in state.done and list((jobs_dir / t.job_name).glob("*/result.json")):
                # Finished while no runner was alive: its verifier rerun and snapshot cleanup are due.
                for d in [jobs_dir / t.job_name] + sorted(jobs_dir.glob(f"{t.job_name}__r*")):
                    if d.is_dir():
                        verifier_rerun(d, ROOT / "tasks" / t.task, env)
                        remove_snapshots(d)
                state.done.append(t.job_name)
                ledger_add(harness.name, jobs_dir / t.job_name)
    def attempts_so_far(t: Trial) -> list[Path]:
        return [d for d in [jobs_dir / t.job_name] + sorted(jobs_dir.glob(f"{t.job_name}__r*")) if d.is_dir()]

    if not dry_run:  # attempts cut off by a stopped runner or host: count their tokens, then retry
        for t in trials:
            for d in attempts_so_far(t):
                rec = record_interrupted(d, harness.name, harness.model)
                if rec:
                    print(f"{msk_now()} {d.name}: interrupted during {rec['phase']}, "
                          f"{units_from_partial(rec) / 1e6:.2f}M units recorded, trial will be retried", flush=True)

    if not dry_run:  # a trial whose last attempt failed on infrastructure gets its remaining retries
        for t in trials:
            tries = attempts_so_far(t)
            if t.job_name in state.done and tries and (infra_failure(tries[-1]) or arm_not_applied(tries[-1], arms[t.arm])) \
                    and len(tries) <= MAX_INFRA_RETRIES:
                state.done.remove(t.job_name)
    todo = [t for t in trials if t.job_name not in state.done]
    if not dry_run:
        state.stopped = None
        state.usd_spent_window = ledger_spent(harness.name, window_start)
        dollars = ledger_spent(harness.name, window_start, "cost_est_usd")
        if state.usd_spent_window >= units_budget or dollars >= usd_budget:
            state.stopped = f"budget already used: {state.usd_spent_window/1e6:.1f}M units, ${dollars:.2f}"
            state_path.write_text(json.dumps(asdict(state), indent=1))
            print(f"STOP: {state.stopped}")
            return state

    def save():
        state_path.write_text(json.dumps(asdict(state), indent=1))

    def one(t: Trial):
        if dry_run:
            return t, 0, " ".join(shlex.quote(c) for c in harbor_cmd(t, harness, arms[t.arm], jobs_dir, mounts, snapshot=True))
        rc = 0
        name = t.job_name
        for attempt in range(len(attempts_so_far(t)), MAX_INFRA_RETRIES + 1):
            name = t.job_name if attempt == 0 else f"{t.job_name}__r{attempt}"
            dirs = arm_host_dirs(arms[t.arm], mounts)
            h_start = tree_hash(dirs)
            with open(jobs_dir / f"{name}.runner.log", "w") as f:
                rc = subprocess.run(harbor_cmd(t, harness, arms[t.arm], jobs_dir, mounts, name, snapshot=True),
                                    cwd=ROOT, env=env, stdout=f, stderr=subprocess.STDOUT).returncode
            try:
                for rec in verifier_rerun(jobs_dir / name, ROOT / "tasks" / t.task, env):
                    print(f"{msk_now()} {name}: verifier timeout, rerun on snapshot: {rec['outcome']}"
                          + (f" reward={rec['reward']}" if "reward" in rec else ""), flush=True)
            finally:
                remove_snapshots(jobs_dir / name)
            h_end = tree_hash(dirs)
            trial_hash[name] = h_start
            changed = None
            if h_start != arm_ref.get(t.arm) or h_end != arm_ref.get(t.arm):
                changed = "arm directory content changed or differs from the batch reference"
            why = infra_failure(jobs_dir / name) or changed or arm_not_applied(jobs_dir / name, arms[t.arm])
            if not why:
                break
            print(f"{msk_now()} {name}: infrastructure failure {why}, retry {attempt + 1}/{MAX_INFRA_RETRIES}", flush=True)
        return t, rc, name

    if not dry_run:
        sweep_snapshots(own=jobs_dir)
    completed_here = 0
    arm_ref = {} if dry_run else {name: tree_hash(arm_host_dirs(a, mounts)) for name, a in arms.items()}
    trial_hash: dict[str, str | None] = {}
    if codex_weekly_start is not None:
        state.codex_weekly_start = codex_weekly_start
    codex_pause = {"until": 0.0}

    def paced_next():
        t = next(pending, None)
        if t is not None and not dry_run and codex_pause["until"] > time.time():
            w = codex_pause["until"] - time.time()
            print(f"{msk_now()} pace: plan 5-hour window full enough, waiting {w/60:.0f} min", flush=True)
            time.sleep(w)
        if t is not None and (pace_units_5h or pace_usd_5h) and not dry_run:
            while (w := max(pace_wait_seconds(harness.name, pace_units_5h) if pace_units_5h else 0.0,
                            pace_wait_seconds(harness.name, pace_usd_5h, field_name="cost_est_usd") if pace_usd_5h else 0.0)) > 0:
                print(f"{msk_now()} pace: 5-hour window full, waiting {w/60:.0f} min")
                time.sleep(min(w, 600))
        announced = False
        while t is not None and not dry_run and (disk_pause_gib or disk_stop_gib):
            free = host_free_gib()
            ds = disk_state(free, disk_pause_gib, disk_stop_gib)
            if ds == "stop":
                state.stopped = f"host disk free {free:.1f} GiB < {disk_stop_gib:g} GiB"
                print(f"{msk_now()} disk stop: {state.stopped}", flush=True)
                return None
            if ds == "go":
                if announced:
                    print(f"{msk_now()} disk resume: host disk free {free:.1f} GiB", flush=True)
                break
            if not announced:
                print(f"{msk_now()} disk pause: host disk free {free:.1f} GiB < {disk_pause_gib:g} GiB", flush=True)
                announced = True
            time.sleep(disk_check_s)
        return t

    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        pending = iter(todo)
        running = {}
        for _ in range(concurrency):
            t = paced_next()
            if t:
                running[pool.submit(one, t)] = t
        while running:
            fut = next(as_completed(running))
            t = running.pop(fut)
            t, rc, info = fut.result()
            if dry_run:
                print(info)
            else:
                tdir = jobs_dir / info  # the last attempt's job directory
                hits = limit_hits(tdir)
                rl = codex_rate_limits(tdir) if harness.name == "codex" else {}
                wk = rl.get("weekly")
                cw = claude_windows(tdir) if harness.name == "claude-code" else {}
                if cw.get("five_hour") is not None and cw["five_hour"] >= claude_five_hour_pause:
                    codex_pause["until"] = float(cw.get("five_hour_resets") or time.time() + 1800)  # until the window resets
                if cw.get("seven_day") is not None:
                    if claude_week_start is None:
                        claude_week_start = cw["seven_day"]
                    state.codex_weekly_last = cw["seven_day"] * 100
                    if claude_week_cap_action == "pause" and cw["seven_day"] >= claude_week_cap:
                        reset = float(cw.get("seven_day_resets") or 0)
                        until = min(reset, time.time() + week_pause_probe_s) if reset > time.time() else time.time() + week_pause_probe_s
                        codex_pause["until"] = max(codex_pause["until"], until)
                        print(f"{msk_now()} pause: account 7-day window {cw['seven_day']:.0%} >= {claude_week_cap:.0%}", flush=True)
                if rolling_week and cw.get("seven_day_resets"):
                    window_start = utc_iso(float(cw["seven_day_resets"]) - 7 * 86400)
                if rl.get("five_hour") is not None and rl["five_hour"] >= codex_pace_pct:
                    codex_pause["until"] = time.time() + rl.get("five_hour_resets_s", 3600)
                if wk is not None:
                    if state.codex_weekly_start is None:
                        state.codex_weekly_start = wk
                    state.codex_weekly_last = wk
                state.done.append(t.job_name)
                for prev in sorted(jobs_dir.glob(f"{t.job_name}__r*")) + [jobs_dir / t.job_name]:
                    if prev.is_dir() and prev != tdir:
                        ledger_add(harness.name, prev, trial_hash.get(prev.name))  # failed attempts
                ledger_add(harness.name, tdir, trial_hash.get(tdir.name))
                # From the ledger, not a running sum: the limit week can roll over during a batch.
                state.usd_spent_window = ledger_spent(harness.name, window_start)
                dollars = ledger_spent(harness.name, window_start, "cost_est_usd")
                completed_here += 1
                print(f"{msk_now()} {t.job_name} rc={rc} week={state.usd_spent_window/1e6:.1f}M units ${dollars:.2f}"
                      + (f" codex-weekly={wk}%" if wk is not None else ""), flush=True)
                if hits:
                    state.stopped = "limit marker: " + hits[0][:300]
                elif wk is not None and state.codex_weekly_start is not None and wk - state.codex_weekly_start > weekly_budget_pp:
                    state.stopped = f"codex weekly usage +{wk - state.codex_weekly_start:.1f} pp > {weekly_budget_pp} pp"
                elif claude_week_cap_action == "stop" and cw.get("seven_day") is not None and cw["seven_day"] >= claude_week_cap:
                    state.stopped = f"claude plan week utilization {cw['seven_day']:.0%} >= cap {claude_week_cap:.0%}"
                elif claude_week_relative_stop and cw.get("seven_day") is not None \
                        and (cw["seven_day"] - claude_week_start) * 100 >= weekly_budget_pp:
                    state.stopped = f"claude plan week utilization {cw['seven_day']:.0%} (+{(cw['seven_day']-claude_week_start)*100:.0f} pp)"
                elif wk is not None and wk >= codex_weekly_cap:
                    state.stopped = f"codex weekly usage {wk}% >= cap {codex_weekly_cap}%"
                elif state.usd_spent_window >= units_budget:
                    state.stopped = f"week units {state.usd_spent_window/1e6:.1f}M >= budget {units_budget/1e6:.1f}M"
                elif dollars >= usd_budget:
                    state.stopped = f"week $ equivalent {dollars:.2f} >= budget {usd_budget:.2f}"
                elif stop_after is not None and completed_here >= stop_after:
                    state.stopped = f"checkpoint after {completed_here} trials"
                save()
                if state.stopped:
                    print(f"STOP: {state.stopped}")
                    for f in running:
                        f.cancel()
                    break
            t_next = paced_next() if not state.stopped else None
            if t_next and not state.stopped:
                running[pool.submit(one, t_next)] = t_next
    save()
    if not dry_run and lock.exists():
        lock.unlink()
    return state
