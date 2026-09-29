#!/usr/bin/env python3
"""Token check (METHOD.md 4.1): always-on tokens per arm from the calibration runs, re-bucketing in
tokens, and the scale factor each placebo needs.

  scripts/token_check.py --harness claude-code     reads jobs/pilot/<harness>/token-check
Writes results/pilot/token-check-<harness>.json and prints a table.

Always-on tokens of an arm = prompt tokens of the first model request (input + cache read + cache
write) minus the same number in the baseline arm. The calibration task's instruction is identical in
every arm, so the difference is what the arm adds at session start.
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from skill_placebo.placebo import assign_buckets  # noqa: E402

JOB_ARM = re.compile(r"^b\d+-\d+__[^_]+(?:-[^_]+)*__(?P<arm>.+?)__")


def first_prompt_tokens(trial_dir: Path) -> int | None:
    tj = trial_dir / "agent" / "trajectory.json"
    if not tj.exists():
        return None
    for step in json.loads(tj.read_text()).get("steps") or []:
        m = step.get("metrics") or {}
        if m.get("prompt_tokens"):
            return int(m["prompt_tokens"])
    return None


def recheck(harness: str):
    first = json.loads((ROOT / "results" / "pilot" / f"token-check-{harness}.json").read_text())
    b0 = first["baseline_first_prompt_tokens"]
    buckets = json.loads((ROOT / "placebo" / "buckets.json").read_text())
    base = ROOT / "jobs" / "pilot" / harness / "token-recheck"
    out, ok = {}, True
    for res in base.glob("*/*/result.json"):
        m = JOB_ARM.match(res.parent.parent.name)
        if not m:
            continue
        bid = m.group("arm").removeprefix("placebo-")
        tok = first_prompt_tokens(res.parent)
        delta = tok - b0 if tok is not None else None
        members = buckets[bid]["bucket"]["members"]
        devs = {s: round(delta / first["always_on_tokens"][f"skill-{s}"] - 1, 4) for s in members} if delta else {}
        ok &= bool(devs) and all(abs(d) <= 0.10 for d in devs.values())
        out[bid] = {"placebo_tokens": delta, "member_tokens": {s: first["always_on_tokens"][f"skill-{s}"] for s in members}, "deviation": devs}
        print(f"{bid}: placebo +{delta} tok; " + ", ".join(f"{s} {d:+.1%}" for s, d in devs.items()))
    (ROOT / "results" / "pilot" / f"token-recheck-{harness}.json").write_text(json.dumps({"all_within_10pct": ok, "buckets": out}, indent=1) + "\n")
    expected = [k for k in buckets if k.startswith("cc-" if harness == "claude-code" else "cx-")]
    ok = ok and set(out) >= set(expected)  # no data for a placebo is not a pass
    print("all placebos within +-10% of every member:", ok, f"({len(out)}/{len(expected)} measured)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--harness", default="claude-code")
    ap.add_argument("--recheck", action="store_true", help="compare rescaled placebos (token-recheck) with the members measured in token-check")
    a = ap.parse_args()
    if a.recheck:
        return recheck(a.harness)
    base = ROOT / "jobs" / "pilot" / a.harness / "token-check"
    per_arm = {}
    for res in base.glob("*/*/result.json"):
        m = JOB_ARM.match(res.parent.parent.name)
        if m:
            per_arm[m.group("arm")] = first_prompt_tokens(res.parent)
    if per_arm.get("baseline") is None:
        sys.exit("no baseline calibration run with token data")
    b0 = per_arm["baseline"]
    delta = {arm: (t - b0 if t is not None else None) for arm, t in per_arm.items() if arm != "baseline"}
    skills = {arm.removeprefix("skill-"): d for arm, d in delta.items() if arm.startswith("skill-") and d is not None}
    placebos = {arm.removeprefix("placebo-"): d for arm, d in delta.items() if arm.startswith("placebo-") and d is not None}
    buckets = assign_buckets(skills)
    prefix = "cc" if a.harness == "claude-code" else "cx"
    current = json.loads((ROOT / "placebo" / "buckets.json").read_text())
    plan = []
    for i, members in enumerate(buckets, 1):
        target = sum(skills[m] for m in members) / len(members)
        # the existing placebo whose members overlap most, for the scale factor
        old = max((bid for bid in current if bid.startswith(prefix)),
                  key=lambda bid: len(set(current[bid]["members"]) & set(members)))
        measured = placebos.get(old)
        plan.append({"bucket": f"{prefix}-{i}", "members": members, "target_tokens": round(target),
                     "member_tokens": {m: skills[m] for m in members},
                     "from_placebo": old, "placebo_tokens_now": measured,
                     "scale": round(target / measured, 4) if measured else None})
    out = {"harness": a.harness, "baseline_first_prompt_tokens": b0, "always_on_tokens": delta, "buckets": plan}
    dst = ROOT / "results" / "pilot" / f"token-check-{a.harness}.json"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(out, indent=1) + "\n")
    print(f"baseline first prompt: {b0} tokens")
    for arm, d in sorted(delta.items(), key=lambda kv: (kv[1] is None, kv[1])):
        print(f"  {arm:32s} +{d}")
    for p in plan:
        print(f"{p['bucket']}: {p['members']} target {p['target_tokens']} tok; {p['from_placebo']} now {p['placebo_tokens_now']} -> scale {p['scale']}")


if __name__ == "__main__":
    main()
