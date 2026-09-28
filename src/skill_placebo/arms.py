"""Arms per harness (METHOD.md sections 3, 4).

Every plugin directory (vendored skills and placebo plugins) is bind-mounted read-only into every
container of every arm at /opt/plugins/<id>. Whether a plugin loads is decided only by the arm's
environment variables, so the file systems of the arms are identical.
"""
from __future__ import annotations

import json
from pathlib import Path

from .runner import ROOT, Arm

VENDOR = ROOT / "vendor"
PLACEBO_DIR = ROOT / "arms" / "placebo"
MOUNT_ROOT = "/opt/plugins"

# Priority order (never independently measured first; METHOD.md section 3).
PRIORITY = [
    "agent-skills", "mattpocock", "i-have-adhd", "planning-with-files", "compound-engineering",
    "karpathy", "superpowers", "ponytail", "caveman",
]

# How each skill is installed in Claude Code, as its author documents it.
CLAUDE_INSTALL = {
    "karpathy": {"SP_CLAUDE_MD": f"{MOUNT_ROOT}/karpathy/CLAUDE.md"},  # the single CLAUDE.md (README option B)
}


def placebo_bucket_of(skill: str, harness: str = "claude-code") -> str:
    buckets = json.loads((ROOT / "placebo" / "buckets.json").read_text())
    prefix = "cc-" if harness == "claude-code" else "cx-"
    for bid, b in buckets.items():
        if bid.startswith(prefix) and skill in b["members"]:
            return bid
    raise KeyError(f"{skill} has no {harness} placebo bucket")


def mounts() -> str:
    dirs = {p.name: p for p in sorted(VENDOR.iterdir()) if p.is_dir()}
    dirs.update({f"placebo-{p.name}": p for p in sorted(PLACEBO_DIR.iterdir()) if p.is_dir()})
    return json.dumps([
        {"type": "bind", "source": str(p.resolve()), "target": f"{MOUNT_ROOT}/{name}", "read_only": True}
        for name, p in sorted(dirs.items())
    ])


def claude_arms(skills: list[str]) -> dict[str, Arm]:
    arms = {"baseline": Arm("baseline")}
    for s in skills:
        env = CLAUDE_INSTALL.get(s, {"CLAUDE_CODE_PLUGIN_DIRS": f"{MOUNT_ROOT}/{s}"})
        arms[f"skill-{s}"] = Arm(f"skill-{s}", tuple(a for k, v in env.items() for a in ("--ae", f"{k}={v}")))
        b = placebo_bucket_of(s)
        arms.setdefault(f"placebo-{b}", Arm(f"placebo-{b}", ("--ae", f"CLAUDE_CODE_PLUGIN_DIRS={MOUNT_ROOT}/placebo-{b}")))
    return arms
