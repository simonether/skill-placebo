#!/usr/bin/env python3
"""Pre-registered analysis of a batch (METHOD.md sections 8-9): every skill vs its placebo (verdicts,
Holm), every skill and placebo vs baseline, secondary outcomes. Output schema: docs/launch/RESULTS_SCHEMA.md.

  scripts/analyze.py jobs/main/claude-code --harness claude-code --out results/main/claude-code.json
  scripts/analyze.py jobs/pilot/claude-code/kill --harness claude-code --out /tmp/check.json   # pilot check
Per trial the last attempt counts; attempts that failed on infrastructure, where the arm did not reach
the agent, or that were interrupted are excluded (and counted in meta). Read-only on jobs/.
"""
import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from skill_placebo.analysis import compare, verdicts  # noqa: E402
from skill_placebo.arms import PRIORITY, claude_arms, codex_arms, placebo_bucket_of  # noqa: E402
from skill_placebo.collect import trial_row  # noqa: E402
from skill_placebo.harnesses import HARNESSES  # noqa: E402
from skill_placebo.runner import arm_not_applied, infra_failure  # noqa: E402

# Secondary outcomes compared as ratios (METHOD.md section 8); key -> row field or function.
METRICS = {
    "cost": lambda r: r["cost_est_usd"],
    "tokens": lambda r: (r["n_input"] or 0) + (r["n_output"] or 0),
    "output_tokens": lambda r: r["n_output"] or 0,
    "agent_seconds": lambda r: r.get("agent_seconds"),
}


def agent_seconds(res: Path) -> float | None:
    r = json.loads(res.read_text())
    a = r.get("agent_execution") or {}
    if not a.get("started_at") or not a.get("finished_at"):
        return None
    f = lambda s: datetime.fromisoformat(s.replace("Z", "+00:00"))  # noqa: E731
    return (f(a["finished_at"]) - f(a["started_at"])).total_seconds()


def collect_rows(jobs: Path, arms: dict) -> tuple[dict, dict]:
    by_trial = defaultdict(list)
    for d in jobs.glob("b*__*"):
        if d.is_dir():
            by_trial[d.name.split("__r")[0]].append(d)
    rows, excluded = [], defaultdict(int)
    for base, attempts in by_trial.items():
        last = sorted(attempts, key=lambda p: (len(p.name), p.name))[-1]
        arm = base.split("__")[2]
        if (last / "interrupted.json").exists():
            excluded["interrupted"] += 1
            continue
        why = infra_failure(last) or (arm_not_applied(last, arms[arm]) if arm in arms else "unknown arm")
        if why:
            excluded[f"excluded: {why}"] += 1
            continue
        for res in last.glob("*/result.json"):
            r = trial_row(res)
            if r and r["passed"] is not None:
                r["agent_seconds"] = agent_seconds(res)
                r["arm"] = arm
                rows.append(r)
    return rows, dict(excluded)


def arm_data(rows, arm, metric):
    out = defaultdict(list)
    for r in rows:
        v = METRICS[metric](r)
        if r["arm"] == arm and v is not None:
            out[r["task"]].append((v, bool(r["passed"])))
    return dict(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("jobs")
    ap.add_argument("--harness", default="claude-code")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    arms = claude_arms(PRIORITY) if a.harness == "claude-code" else codex_arms(PRIORITY)
    rows, excluded = collect_rows(Path(a.jobs), arms)
    present = {r["arm"] for r in rows}
    skills = [s for s in PRIORITY if f"skill-{s}" in present]
    comps, extra = {}, {}
    for s in skills:
        p_arm = f"placebo-{placebo_bucket_of(s, a.harness)}"
        if p_arm not in present:
            continue
        comps[s] = compare(arm_data(rows, f"skill-{s}", "cost"), arm_data(rows, p_arm, "cost"))
        out_s = compare(arm_data(rows, f"skill-{s}", "output_tokens"), arm_data(rows, p_arm, "output_tokens"))
        extra[s] = {"placebo": p_arm, "output_tokens_vs_placebo": {"ratio": out_s.ratio, "ratio_ci": out_s.ratio_ci},
                    "mean_output_tokens_skill": out_s.cost_treat, "mean_output_tokens_placebo": out_s.cost_control}
    table = {s: {**v, **extra[s]} for s, v in verdicts(comps).items()} if comps else {}
    vs_base, placebo_vs_base = {}, {}
    if "baseline" in present:
        for arm in sorted(present - {"baseline"}):
            m = {}
            for metric in METRICS:
                c = compare(arm_data(rows, arm, metric), arm_data(rows, "baseline", metric))
                m[f"{metric}_vs_baseline"] = {"ratio": c.ratio, "ratio_ci": c.ratio_ci, "ratio_p": c.ratio_p}
                if metric == "cost":
                    m["pass_vs_baseline"] = {"diff_pp": c.diff_pp, "diff_ci_pp": c.diff_ci_pp, "diff_p": c.diff_p,
                                             "pass_arm": c.pass_treat, "pass_baseline": c.pass_control}
            (vs_base if arm.startswith("skill-") else placebo_vs_base)[arm.split("-", 1)[1]] = m
    per_arm = defaultdict(int)
    for r in rows:
        per_arm[r["arm"]] += 1
    started = sorted(r["started"] for r in rows if r.get("started"))
    h = HARNESSES[a.harness]
    meta = {"harness": a.harness, "model": h.model.split("/")[-1], "cli_version": h.kwargs.get("version"),
            "n_trials": len(rows), "n_tasks": len({r["task"] for r in rows}),
            "n_per_arm": max(per_arm.values()) if per_arm else 0, "trials_per_arm": dict(sorted(per_arm.items())),
            "excluded": excluded, "verifier_reruns": sum(1 for r in rows if r.get("verifier_rerun")),
            "pins_seen": sorted({(r.get("cli_version"), r.get("session_model")) for r in rows}),
            "first_trial": started[0] if started else None, "last_trial": started[-1] if started else None,
            "date": (started[-1] or "")[:10] if started else None, "source": str(Path(a.jobs))}
    out = {"harness": a.harness, "meta": meta, "comparisons": table, "vs_baseline": vs_base,
           "placebo_vs_baseline": placebo_vs_base}
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(out, indent=1, default=list) + "\n")
    for s, c in table.items():
        print(f"{s:22s} vs {c['placebo']:14s} R={c['ratio']:.2f} [{c['ratio_ci'][0]:.2f}, {c['ratio_ci'][1]:.2f}] {c['verdict']}")
    print(f"{len(rows)} trials, excluded {excluded}, -> {a.out}")


if __name__ == "__main__":
    main()
