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

# Priority order by stars (METHOD.md section 3).
# Reduced designs drop from the end.
PRIORITY = [
    "superpowers", "mattpocock", "karpathy", "ponytail", "caveman",
    "agent-skills", "i-have-adhd", "planning-with-files", "compound-engineering",
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
    if MKT_DIR.exists():
        dirs.update({f"mkt-{p.name}": p for p in sorted(MKT_DIR.iterdir()) if p.is_dir()})
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


# --- Codex ---------------------------------------------------------------------------------------
MKT_DIR = ROOT / "arms" / "codex-mkt"

# Skills with a documented Codex install that works without a per-session manual command.
# plugin name as in the author's Codex marketplace; None = installed as plain skills (npx skills).
CODEX_PLUGINS = {
    "superpowers": "superpowers",
    "mattpocock": None,
    "ponytail": "ponytail",
    "agent-skills": "agent-skills",
    "planning-with-files": "planning-with-files",
    "compound-engineering": "compound-engineering",
}
NOT_ON_CODEX = {
    "karpathy": "the author documents no Codex install",
    "caveman": "on Codex the author's install needs a manual /caveman in every session",
    "i-have-adhd": "on Codex the author's install needs an explicit $i-have-adhd in every session",
}


def write_codex_marketplaces() -> None:
    """One local marketplace per plugin skill, pointing at the pinned checkout mounted in the container.
    The authors' own marketplace files can point at GitHub HEAD (ponytail does), which would bypass the pin."""
    for sid, plugin in CODEX_PLUGINS.items():
        if not plugin:
            continue
        d = MKT_DIR / sid / ".agents" / "plugins"
        d.mkdir(parents=True, exist_ok=True)
        (d / "marketplace.json").write_text(json.dumps({
            "name": f"{sid}-pinned",
            "plugins": [{"name": plugin, "source": {"source": "url", "url": f"{MOUNT_ROOT}/{sid}"},
                         "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
                         "category": "Developer Tools"}],
        }, indent=2) + "\n")


def _mattpocock_skill_dirs(root: Path) -> list[Path]:
    return [root / p for p in json.loads((VENDOR / "mattpocock" / ".claude-plugin" / "plugin.json").read_text())["skills"]]


def codex_arms(skills: list[str]) -> dict[str, Arm]:
    arms = {"baseline": Arm("baseline")}
    for s in skills:
        if s in NOT_ON_CODEX:
            continue
        plugin = CODEX_PLUGINS[s]
        if plugin:
            args = ("--ae", f"SP_CODEX_MARKETPLACES={MOUNT_ROOT}/mkt-{s}", "--ae", f"SP_CODEX_PLUGINS={plugin}@{s}-pinned")
        else:
            args = tuple(a for d in _mattpocock_skill_dirs(VENDOR / "mattpocock") for a in ("--skill", str(d)))
        arms[f"skill-{s}"] = Arm(f"skill-{s}", args)
        b = placebo_bucket_of(s, "codex")
        if f"placebo-{b}" in arms:
            continue
        if plugin:
            pargs = ("--ae", f"SP_CODEX_MARKETPLACES={MOUNT_ROOT}/placebo-{b}",
                     "--ae", f"SP_CODEX_PLUGINS=session-notes-{b}@session-notes-{b}-dev")
        else:  # mirror a skills-only install with the placebo's skills
            pargs = tuple(a for d in sorted((PLACEBO_DIR / b / "skills").iterdir()) for a in ("--skill", str(d)))
        arms[f"placebo-{b}"] = Arm(f"placebo-{b}", pargs)
    return arms
