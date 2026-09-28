#!/usr/bin/env python3
"""Measure the always-on context each skill adds in Claude Code at session start (METHOD.md 4.1).

For every vendored skill (vendor/<id>, scripts/vendor_skills.py):
  listing  = characters of "name: description" for every skill/agent/command the plugin exposes
             (frontmatter of SKILL.md, agents/*.md, commands/*.md the manifest points at)
  hook     = characters of the text SessionStart hooks inject (hooks run for real, with HOME and
             CLAUDE_CONFIG_DIR in a scratch directory so nothing touches the real ~/.claude)
  memory   = characters of CLAUDE.md-style always-on files the documented install adds
Also records Claude Code's own estimate (`claude plugin details`, always-on tokens).
Writes placebo/always_on.json.
"""
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "vendor"

# How each skill is installed on Claude Code, per its author (docs/research/2026-09-28-skills-census.md).
INSTALL = {
    "agent-skills": {"plugin": "."},
    "mattpocock": {"plugin": "."},
    "i-have-adhd": {"plugin": ".", "home_files": [".claude/.i-have-adhd-always"]},  # documented always-on flag
    "planning-with-files": {"plugin": "."},
    "compound-engineering": {"plugin": "."},
    "karpathy": {"memory": "CLAUDE.md"},  # README option B: the single CLAUDE.md file
    "superpowers": {"plugin": "."},
    "ponytail": {"plugin": ".", "home_files": [".claude/.ponytail-statusline-nudged"]},  # all arms: no statusline nudge
    "caveman": {"plugin": ".", "home_files": [".claude/.caveman-nudge-shown"]},
}

FM = re.compile(r"^---\s*\n(.*?)\n---", re.S)


def frontmatter(path: Path) -> dict:
    import yaml

    m = FM.match(path.read_text(errors="replace"))
    if not m:
        return {}
    try:
        d = yaml.safe_load(m.group(1))
    except yaml.YAMLError:
        return {}
    return d if isinstance(d, dict) else {}


def plugin_details(plugin_dir: Path, cfg: Path, home: Path):
    """Claude Code's own view: always-on token estimate and the names of listed skills and agents."""
    env = {"PATH": os.environ["PATH"], "HOME": str(home), "CLAUDE_CONFIG_DIR": str(cfg),
           "CLAUDE_CODE_PLUGIN_DIRS": str(plugin_dir)}
    lst = subprocess.run(["claude", "plugin", "list"], env=env, capture_output=True, text=True).stdout
    m = re.search(r"❯ (\S+)@inline", lst)
    if not m:
        return None, {}
    det = subprocess.run(["claude", "plugin", "details", m.group(1)], env=env, capture_output=True, text=True).stdout
    tok = re.search(r"Always-on:\s*~?([\d,.]+)(k?)\s*tok", det)
    est = None if not tok else float(tok.group(1).replace(",", "")) * (1000 if tok.group(2) else 1)
    names = {}
    for kind in ("Skills", "Agents"):
        mm = re.search(rf"^  {kind} \(\d+\)\s+(.*)$", det, re.M)
        names[kind] = [x.strip() for x in mm.group(1).split(",")] if mm else []
    return est, names


def _candidates(plugin_dir: Path, sub: str, pattern: str):
    return [p for p in plugin_dir.glob(f"{sub}/{pattern}") if "/." not in str(p.relative_to(plugin_dir))]


def listing_chars(plugin_dir: Path, names: dict) -> int:
    """Sum of len(name) + len(description) over exactly the components Claude Code lists."""
    total = 0
    skills = _candidates(plugin_dir, "skills", "**/SKILL.md")
    cmds = _candidates(plugin_dir, "commands", "*.md") + _candidates(plugin_dir, ".claude/commands", "*.md")
    agents = _candidates(plugin_dir, "agents", "*.md")
    for n in names.get("Skills", []):
        hit = None
        for f in skills:
            fm = frontmatter(f)
            if fm.get("name") == n or f.parent.name == n:
                hit = fm
                break
        if hit is None:
            for f in cmds:
                if f.stem == n:
                    hit = frontmatter(f)
                    break
        total += len(n) + len(str((hit or {}).get("description", "")))
    for n in names.get("Agents", []):
        fm = next((frontmatter(f) for f in agents if f.stem == n or frontmatter(f).get("name") == n), {})
        total += len(n) + len(str(fm.get("description", "")))
    return total


def run_session_start_hooks(plugin_dir: Path, home: Path, cfg: Path) -> str:
    manifest = plugin_dir / ".claude-plugin" / "plugin.json"
    hooks = {}
    if manifest.exists():
        pj = json.loads(manifest.read_text())
        h = pj.get("hooks")
        if isinstance(h, dict):
            hooks = h.get("hooks", h)
        elif isinstance(h, str):
            hooks = json.loads((plugin_dir / h).read_text()).get("hooks", {})
    if not hooks and (plugin_dir / "hooks" / "hooks.json").exists():
        hooks = json.loads((plugin_dir / "hooks" / "hooks.json").read_text()).get("hooks", {})
    texts = []
    for group in hooks.get("SessionStart", []):
        if group.get("matcher") and not re.search(group["matcher"], "startup"):
            continue
        for hk in group.get("hooks", []):
            if hk.get("type") != "command":
                continue
            cmd = hk["command"].replace("${CLAUDE_PLUGIN_ROOT}", str(plugin_dir))
            env = {"PATH": os.environ["PATH"], "HOME": str(home), "CLAUDE_CONFIG_DIR": str(cfg),
                   "CLAUDE_PLUGIN_ROOT": str(plugin_dir), "CLAUDE_PROJECT_DIR": str(home / "app")}
            ev = json.dumps({"hook_event_name": "SessionStart", "source": "startup", "session_id": "x",
                             "cwd": str(home / "app"), "transcript_path": str(home / "t.jsonl")})
            r = subprocess.run(cmd, shell=True, input=ev, env=env, capture_output=True, text=True, cwd=home / "app", timeout=60)
            out = r.stdout.strip()
            try:
                j = json.loads(out)
                out = ((j.get("hookSpecificOutput") or {}).get("additionalContext")) or j.get("additionalContext") or j.get("systemMessage") or ""
            except json.JSONDecodeError:
                pass
            texts.append(out)
    return "\n".join(t for t in texts if t)


def main():
    result = {}
    for sid, how in INSTALL.items():
        d = VENDOR / sid
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            cfg = home / ".claude"
            (home / "app").mkdir()
            cfg.mkdir()
            for f in how.get("home_files", []):
                (home / f).parent.mkdir(parents=True, exist_ok=True)
                (home / f).touch()
            row = {"listing_chars": 0, "hook_chars": 0, "memory_chars": 0, "cc_estimate_tokens": None}
            if "plugin" in how:
                pdir = (d / how["plugin"]).resolve()
                est, names = plugin_details(pdir, cfg, home)
                row["cc_estimate_tokens"] = est
                row["listing_chars"] = listing_chars(pdir, names)
                row["listed_skills"] = len(names.get("Skills", []))
                row["listed_agents"] = len(names.get("Agents", []))
                row["hook_chars"] = len(run_session_start_hooks(pdir, home, cfg))
            if "memory" in how:
                row["memory_chars"] = len((d / how["memory"]).read_text())
            row["total_chars"] = row["listing_chars"] + row["hook_chars"] + row["memory_chars"]
            result[sid] = row
            print(f"{sid:22s} listing={row['listing_chars']:6d} hook={row['hook_chars']:6d} memory={row['memory_chars']:5d} "
                  f"total={row['total_chars']:6d} cc_est_tok={row['cc_estimate_tokens']}")
    out = ROOT / "placebo" / "always_on.json"
    out.write_text(json.dumps(result, indent=1) + "\n")


if __name__ == "__main__":
    sys.exit(main())
