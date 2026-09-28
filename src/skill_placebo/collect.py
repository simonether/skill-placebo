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


def trial_row(res: Path) -> dict | None:
    """One trial's row from its result.json (jobs/<...>/<job>/<trial>/result.json)."""
    tdir = res.parent
    job = tdir.parent.name
    r = _load(res)
    if not r.get("task_name"):
        return None
    m = JOB_RE.match(job)
    meta = m.groupdict() if m else {"block": "", "order": "", "harness": "", "arm": job, "task": r["task_name"]}
    a = r.get("agent_result") or {}
    rw = (r.get("verifier_result") or {}).get("rewards") or {}
    ex = (_load(tdir / "agent" / "trajectory.json").get("final_metrics") or {}).get("extra") or {}
    cw = ex.get("total_cache_creation_input_tokens") or ex.get("total_cache_write_input_tokens") or 0
    model = ((r.get("agent_info") or {}).get("model_info") or {}).get("name", "")
    n_in, n_c, n_out = a.get("n_input_tokens") or 0, a.get("n_cache_tokens") or 0, a.get("n_output_tokens") or 0
    reward = rw.get("reward")
    turns_file = tdir / "agent" / "approval_turns.txt"
    return {
        **meta,
        "trial": r.get("trial_name"),
        "agent": (r.get("agent_info") or {}).get("name"),
        "agent_version": (r.get("agent_info") or {}).get("version"),
        "model": model,
        "task_checksum": r.get("task_checksum"),
        "reasoning_effort": (((r.get("config") or {}).get("agent") or {}).get("kwargs") or {}).get("reasoning_effort"),
        "reward": reward,
        "passed": None if reward is None else int(float(reward) >= 1.0),
        "exception": (r.get("exception_info") or {}).get("exception_type"),
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
