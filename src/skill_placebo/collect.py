"""Collect per-trial rows from Harbor job directories (METHOD.md section 8).

Cost is recomputed from recorded token usage at public API list prices, even when the run used a
subscription: it is an estimate by tokens, not money spent, and the tables say so. Harbor's own
cost_usd is kept alongside for comparison.
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

# $/MTok: input, cached input (cache read), cache write (5-min), output. Checked 2026-09-25:
# platform.claude.com/docs/en/about-claude/pricing, developers.openai.com/api/docs/pricing
# (docs/research/2026-09-25-harness-infra.md).
PRICES = {
    "claude-sonnet-5": (2.00, 0.20, 2.50, 10.00),
    "claude-haiku-4-5": (1.00, 0.10, 1.25, 5.00),
    "claude-opus-5-5": (4.00, 0.20, 5.00, 20.00),
    "gpt-6-sol": (2.00, 0.20, 2.50, 10.00),
    "gpt-6-luna": (0.10, 0.01, 0.125, 0.50),
}
PRICES_DATE = "2026-09-25"

JOB_RE = re.compile(r"^b(?P<block>\d+)-(?P<order>\d+)__(?P<harness>[^_]+(?:-[^_]+)*)__(?P<arm>.+?)__(?P<task>.+)$")


def _load(p: Path) -> dict:
    try:
        return json.loads(p.read_text())
    except (OSError, json.JSONDecodeError):
        return {}


def skill_fired(trial_dir: Path) -> int:
    """Count of Skill tool calls (Claude) or SKILL.md reads (Codex) in the ATIF trajectory."""
    tj = _load(trial_dir / "agent" / "trajectory.json")
    n = 0
    for step in tj.get("steps") or []:
        for call in step.get("tool_calls") or []:
            name = call.get("function_name") or ""
            args = json.dumps(call.get("arguments") or {})
            if name == "Skill" or "SKILL.md" in args:
                n += 1
    return n


def units_from_tokens(n_input: int, n_cached: int, n_cache_write: int, n_output: int) -> float:
    """Limit units (METHOD.md amendment 2): uncached input x1 + cache write x1.25 + cache read x0.1 +
    output x5. The same formula used on the owner's own logs to calibrate % of the week per unit."""
    uncached = max(0, n_input - n_cached - n_cache_write)
    return uncached * 1.0 + n_cache_write * 1.25 + n_cached * 0.1 + n_output * 5.0


def cost_from_tokens(model: str, n_input: int, n_cached: int, n_cache_write: int, n_output: int) -> float | None:
    p = PRICES.get(model.split("/")[-1])
    if not p:
        return None
    uncached = max(0, n_input - n_cached - n_cache_write)
    return (uncached * p[0] + n_cached * p[1] + n_cache_write * p[2] + n_output * p[3]) / 1e6


def _is_infra(exc: dict) -> bool:
    t = exc.get("exception_type")
    return t in {"AgentSetupTimeoutError", "EnvironmentStartTimeoutError", "HealthcheckError", "SandboxBuildFailedError"} \
        or (t == "RuntimeError" and "docker" in str(exc.get("exception_message", "")).lower())


def partial_usage(trial_dir: Path) -> dict:
    """Tokens of an attempt that never wrote result.json (runner or host stopped mid-trial), from
    the per-message usage in Claude Code's stream (largest value per message id), in trial_row's
    terms: n_input includes cache reads and writes."""
    msgs: dict[str, dict] = {}
    for p in trial_dir.rglob("claude-code.txt"):
        for line in p.read_text(errors="replace").splitlines():
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(ev, dict) or ev.get("type") != "assistant":
                continue
            m = ev.get("message") or {}
            u = m.get("usage") or {}
            cur = msgs.setdefault(m.get("id") or str(len(msgs)), {})
            for k in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens"):
                cur[k] = max(cur.get(k, 0), u.get(k) or 0)
    tot = {k: sum(m.get(k, 0) for m in msgs.values()) for k in
           ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens")}
    n_c, cw, n_out = tot["cache_read_input_tokens"], tot["cache_creation_input_tokens"], tot["output_tokens"]
    return {"n_input": tot["input_tokens"] + n_c + cw, "n_cached": n_c, "n_cache_write": cw, "n_output": n_out,
            "messages": len(msgs)}


def session_pins(trial_dir: Path) -> dict:
    """CLI versions and models the agent's own session logs report: Claude Code's init events,
    Codex's session_meta and turn_context. Sets, because approval turns start new sessions."""
    ver, models = set(), set()
    for p in trial_dir.rglob("claude-code.txt"):
        for line in p.read_text(errors="replace").splitlines():
            if '"init"' not in line:
                continue
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(ev, dict) and ev.get("subtype") == "init":
                ver.add(ev.get("claude_code_version"))
                models.add(ev.get("model"))
    for p in trial_dir.rglob("rollout-*.jsonl"):
        for line in p.read_text(errors="replace").splitlines():
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            pl = ev.get("payload") or {} if isinstance(ev, dict) else {}
            if ev.get("type") == "session_meta":
                ver.add(pl.get("cli_version"))
            elif ev.get("type") == "turn_context":
                models.add(pl.get("model"))
    return {"cli_versions": sorted(v for v in ver if v), "models": sorted(m for m in models if m)}


def trial_row(res: Path) -> dict | None:
    """One trial's row from its result.json (jobs/<...>/<job>/<trial>/result.json)."""
    tdir = res.parent
    job = tdir.parent.name
    r = _load(res)
    if not r.get("task_name"):
        return None
    attempt = 0
    mm = re.search(r"__r(\d+)$", job)
    if mm:
        attempt, job = int(mm.group(1)), job[: mm.start()]
    m = JOB_RE.match(job)
    meta = m.groupdict() if m else {"block": "", "order": "", "harness": "", "arm": job, "task": r["task_name"]}
    exc = r.get("exception_info") or {}
    a = r.get("agent_result") or {}
    rw = (r.get("verifier_result") or {}).get("rewards") or {}
    ex = (_load(tdir / "agent" / "trajectory.json").get("final_metrics") or {}).get("extra") or {}
    cw = ex.get("total_cache_creation_input_tokens") or ex.get("total_cache_write_input_tokens") or 0
    model = ((r.get("agent_info") or {}).get("model_info") or {}).get("name", "")
    n_in, n_c, n_out = a.get("n_input_tokens") or 0, a.get("n_cache_tokens") or 0, a.get("n_output_tokens") or 0
    reward = rw.get("reward")
    # METHOD.md amendment 9: a verifier timeout is verified once more on the agent's final state;
    # a rerun within the timeout gives the trial's reward, and the episode is flagged.
    vr = _load(tdir / "verifier_rerun.json")
    if exc.get("exception_type") == "VerifierTimeoutError" and vr.get("outcome") == "rerun within timeout":
        reward = vr.get("reward")
    turns_file = tdir / "agent" / "approval_turns.txt"
    pins = session_pins(tdir)
    return {
        **meta,
        "trial": r.get("trial_name"),
        "agent": (r.get("agent_info") or {}).get("name"),
        "agent_version": (r.get("agent_info") or {}).get("version"),
        "model": model,
        "task_checksum": r.get("task_checksum"),
        "reasoning_effort": (((r.get("config") or {}).get("agent") or {}).get("kwargs") or {}).get("reasoning_effort"),
        "reward": reward,
        # No reward: an infrastructure failure is not a trial (excluded, rerun); anything else - agent
        # timeout, verifier timeout on the agent's code, crash - is a failed trial (METHOD.md section 7).
        "passed": (None if _is_infra(exc) else 0) if reward is None else int(float(reward) >= 1.0),
        "exception": exc.get("exception_type"),
        "attempt": attempt,
        "infra_failure": int(_is_infra(exc)),
        "verifier_rerun": vr.get("outcome"),
        "cli_version": ",".join(pins["cli_versions"]),
        "session_model": ",".join(pins["models"]),
        "n_input": n_in, "n_cached": n_c, "n_cache_write": cw, "n_output": n_out,
        "cost_est_usd": cost_from_tokens(model, n_in, n_c, cw, n_out),
        "units": units_from_tokens(n_in, n_c, cw, n_out),
        "cost_harbor_usd": a.get("cost_usd"),
        "skill_fired": skill_fired(tdir),
        "approval_turns": int(turns_file.read_text().strip() or 0) if turns_file.exists() else None,
        "started": r.get("started_at"), "finished": r.get("finished_at"),
    }


def rows(jobs_dir: Path):
    for res in sorted(jobs_dir.glob("*/*/result.json")):
        row = trial_row(res)
        if row:
            yield row


def write_csv(jobs_dir: Path, out: Path) -> int:
    data = list(rows(jobs_dir))
    if not data:
        return 0
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(data[0]))
        w.writeheader()
        w.writerows(data)
    return len(data)
