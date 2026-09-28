#!/usr/bin/env python3
"""Build the placebo plugins for every bucket (METHOD.md 4.1) into arms/placebo/<bucket>/ and check
that each bucket member's always-on length is within +-10% of its placebo.

Buckets are fixed in BUCKETS below and in METHOD.md; lengths come from placebo/always_on.json
(scripts/measure_always_on.py).
"""
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from skill_placebo.placebo import assign_buckets, build, bucket_from_members  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
TOLERANCE = 0.10

# Measured always-on lengths per harness (scripts/measure_always_on.py). The buckets are computed by
# the pre-registered rule in placebo.assign_buckets, not chosen by hand.
SOURCES = {"cc": "always_on.json", "cx": "always_on_codex.json"}
CODEX_SKILLS = ["superpowers", "mattpocock", "ponytail", "agent-skills", "planning-with-files", "compound-engineering"]


# Placebo token model fitted on the first calibration (5 placebos, 29.09, residuals <= 7 tokens):
# tokens ~= a * listing chars + b * hook chars + c * listed entries.
TOKEN_MODEL = (0.2712, 0.2640, 12.004)


def token_targets(harness_prefix: str) -> list[tuple[str, list[str], float]] | None:
    """Buckets and token targets from the token check (results/pilot/token-check-<harness>.json)."""
    name = {"cc": "claude-code", "cx": "codex"}[harness_prefix]
    f = ROOT / "results" / "pilot" / f"token-check-{name}.json"
    if not f.exists():
        return None
    tc = json.loads(f.read_text())
    return [(b["bucket"], b["members"], b["target_tokens"]) for b in tc["buckets"]]


def main():
    out_root = ROOT / "arms" / "placebo"
    if out_root.exists():
        shutil.rmtree(out_root)
    report, ok = {}, True
    plan = []
    for prefix, fname in SOURCES.items():
        data = json.loads((ROOT / "placebo" / fname).read_text())
        if prefix == "cx":
            data = {k: v for k, v in data.items() if k in CODEX_SKILLS}
        tt = token_targets(prefix) if "--tokens" in sys.argv else None
        if tt:
            for bid, members, target in tt:
                plan.append((bid, members, data, target))
        else:
            lengths = {k: v["total_chars"] for k, v in data.items()}
            for i, members in enumerate(assign_buckets(lengths), 1):
                plan.append((f"{prefix}-{i}", members, data, None))
    for bid, members, always_on, target_tokens in plan:
        bodies = {k: v["mean_body_chars"] for k, v in always_on.items()}
        b = bucket_from_members(bid, members, always_on, bodies)
        if target_tokens:
            a, h, c = TOKEN_MODEL
            n = b.n_skills
            while n > 1 and target_tokens - c * n < 0.3 * target_tokens:
                n -= 1  # too many entries for a small target
            per_char = a * b.listing_chars + h * b.hook_chars
            f = (target_tokens - c * n) / per_char if per_char else 1.0
            b.n_skills, b.listing_chars, b.hook_chars = n, round(b.listing_chars * f), round(b.hook_chars * f)
        d = out_root / bid
        if d.exists():
            shutil.rmtree(d)
        r = build(b, d)
        checks = {}
        tc = json.loads((ROOT / "results" / "pilot" / "token-check-claude-code.json").read_text()) if target_tokens else None
        for m in members:
            if target_tokens:  # check in tokens: model prediction for the placebo vs the member's measured tokens
                a, h, c = TOKEN_MODEL
                pred = a * r["listing_chars"] + h * r["hook_chars"] + c * b.n_skills
                real = tc["always_on_tokens"][f"skill-{m}"]
                dev = pred / real - 1
                checks[m] = {"skill_tokens": real, "placebo_tokens_predicted": round(pred), "deviation": round(dev, 4)}
                ok &= abs(dev) <= TOLERANCE
                continue
            real = always_on[m]["total_chars"]
            dev = r["total_chars"] / real - 1
            checks[m] = {"skill_chars": real, "placebo_chars": r["total_chars"], "deviation": round(dev, 4)}
            ok &= abs(dev) <= TOLERANCE
        report[bid] = {**r, "members": checks}
        print(bid, r["total_chars"], "chars", {m: f"{c['deviation']:+.1%}" for m, c in checks.items()})
    (ROOT / "placebo" / "buckets.json").write_text(json.dumps(report, indent=1) + "\n")
    if not ok:
        sys.exit("a bucket member is outside the +-10% tolerance")


if __name__ == "__main__":
    main()
