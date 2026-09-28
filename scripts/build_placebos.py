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
from skill_placebo.placebo import build, bucket_from_members  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
TOLERANCE = 0.10

# Claude Code buckets: always-on characters within +-10% of the bucket mean.
BUCKETS = {
    "cc-a": ["karpathy", "planning-with-files"],
    "cc-b": ["mattpocock"],
    "cc-c": ["superpowers"],
    "cc-d": ["i-have-adhd", "ponytail", "compound-engineering"],
    "cc-e": ["caveman", "agent-skills"],
}


def main():
    always_on = json.loads((ROOT / "placebo" / "always_on.json").read_text())
    bodies = {k: v["mean_body_chars"] for k, v in always_on.items()}
    out_root = ROOT / "arms" / "placebo"
    report, ok = {}, True
    for bid, members in BUCKETS.items():
        b = bucket_from_members(bid, members, always_on, bodies)
        d = out_root / bid
        if d.exists():
            shutil.rmtree(d)
        r = build(b, d)
        checks = {}
        for m in members:
            real = always_on[m]["total_chars"]
            dev = r["total_chars"] / real - 1
            checks[m] = {"skill_chars": real, "placebo_chars": r["total_chars"], "deviation": round(dev, 4)}
            ok &= abs(dev) <= TOLERANCE
        report[bid] = {**r, "members": checks}
        print(bid, r["total_chars"], {m: f"{c['deviation']:+.1%}" for m, c in checks.items()})
    (ROOT / "placebo" / "buckets.json").write_text(json.dumps(report, indent=1) + "\n")
    if not ok:
        sys.exit("a bucket member is outside the +-10% tolerance")


if __name__ == "__main__":
    main()
