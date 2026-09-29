"""Build length-matched placebo plugins (METHOD.md section 4.1).

A placebo bucket is a set of skills whose always-on context lengths lie within +-10% of one target.
Its placebo is a sham plugin in the same format as the real ones (Claude Code and Codex manifests,
a SessionStart hook, a skills directory) whose always-on context is neutral text from
placebo/corpus.md:

  listing  k neutral skills; name + description lengths sum to the members' mean listing length
  hook     a SessionStart hook that injects neutral text of the members' mean hook + memory length
  bodies   each neutral skill body has the members' mean on-invoke body length

The hook only runs `cat` on a prebuilt text file, so it needs no node or python in the container.
Everything is deterministic: the same inputs give byte-identical output.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CORPUS = ROOT / "placebo" / "corpus.md"
TOPICS = [
    "working-directory", "shell", "programs", "source-code", "version-control", "text-formats",
    "networks", "results", "processes", "paths", "configuration", "logs", "encodings", "packages",
    "containers", "variables", "permissions", "timeouts", "builds", "libraries", "modules",
    "scripts", "standard-streams", "exit-codes", "symbolic-links", "virtual-environments",
    "repositories", "directories", "interpreters", "compilers", "caches", "arguments",
    "functions", "exceptions", "versions", "file-systems", "binaries", "command-line",
]


@dataclass
class Bucket:
    id: str
    members: list[str]
    listing_chars: int
    hook_chars: int
    n_skills: int
    body_chars: int


def _paragraphs() -> list[str]:
    text = CORPUS.read_text()
    text = re.sub(r"^# .*\n", "", text)
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]


def neutral_text(n: int, offset: int = 0) -> str:
    """Exactly n characters of corpus text, cycling paragraphs from `offset`, cut at a word boundary
    and padded with spaces only if the cut falls short by a few characters."""
    paras = _paragraphs()
    out, i = [], offset
    while sum(len(p) + 2 for p in out) < n + 200:
        out.append(paras[i % len(paras)])
        i += 1
    text = "\n\n".join(out)[:n]
    cut = text.rfind(" ")
    if cut > n - 40:
        text = text[:cut]
    return text + " " * (n - len(text))


def _sentence_filler(n: int, seed: int) -> str:
    sentences = re.split(r"(?<=\.)\s+", " ".join(p.replace("\n", " ") for p in _paragraphs() if not p.startswith("#")))
    out, i = "", seed
    while len(out) < n:
        out = (out + " " + sentences[i % len(sentences)]).strip()
        i += 1
    out = out[:n]
    cut = out.rfind(" ")
    if cut > n - 30:
        out = out[:cut]
    return out + "." * (n - len(out))


def bucket_from_members(bucket_id: str, members: list[str], always_on: dict, bodies: dict) -> Bucket:
    rows = [always_on[m] for m in members]
    k = len(rows)
    return Bucket(
        id=bucket_id,
        members=members,
        listing_chars=round(sum(r["listing_chars"] for r in rows) / k),
        hook_chars=round(sum(r["hook_chars"] + r["memory_chars"] for r in rows) / k),
        n_skills=max(1, round(sum(r.get("listed_skills", 0) + r.get("listed_agents", 0) for r in rows) / k)),
        body_chars=round(sum(bodies[m] for m in members) / k),
    )


def build(bucket: Bucket, out_dir: Path) -> dict:
    name = f"session-notes-{bucket.id}"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / ".claude-plugin").mkdir(exist_ok=True)
    (out_dir / ".codex-plugin").mkdir(exist_ok=True)
    (out_dir / ".agents" / "plugins").mkdir(parents=True, exist_ok=True)
    (out_dir / "hooks").mkdir(exist_ok=True)
    desc = "Reference notes about the working environment of a session."
    (out_dir / ".claude-plugin" / "plugin.json").write_text(json.dumps(
        {"name": name, "description": desc, "version": "1.0.0", "license": "MIT"}, indent=2) + "\n")
    hooks = {"hooks": {}}
    if bucket.hook_chars:
        # Plain text on stdout, like ponytail's hook: added as context by Claude Code and Codex alike.
        hooks = {"hooks": {"SessionStart": [{"matcher": "startup|clear|compact", "hooks": [
            {"type": "command", "command": "cat \"${CLAUDE_PLUGIN_ROOT}/hooks/session-start.txt\""}]}]}}
        (out_dir / "hooks" / "session-start.txt").write_text(neutral_text(bucket.hook_chars))
    (out_dir / "hooks" / "hooks.json").write_text(json.dumps(hooks, indent=2) + "\n")
    (out_dir / ".codex-plugin" / "plugin.json").write_text(json.dumps(
        {"name": name, "version": "1.0.0", "description": desc, "license": "MIT", "skills": "./skills/",
         "hooks": "./hooks/hooks.json" if bucket.hook_chars else {}}, indent=2) + "\n")
    (out_dir / ".agents" / "plugins" / "marketplace.json").write_text(json.dumps(
        {"name": f"{name}-dev", "interface": {"displayName": "Session notes"},
         # "local" source: Codex copies the directory; a "url" source would try to `git clone` it,
         # and placebo directories are not git repositories (Codex pilot, 29.09).
         "plugins": [{"name": name, "source": {"source": "local", "path": "./"},
                      "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
                      "category": "Developer Tools"}]}, indent=2) + "\n")
    # Skills: names from TOPICS; descriptions sized so that sum(len(name) + len(description)) == listing_chars.
    listing = 0
    if bucket.listing_chars:
        names = [f"notes-{TOPICS[i % len(TOPICS)]}" + (f"-{i // len(TOPICS) + 1}" if i >= len(TOPICS) else "")
                 for i in range(bucket.n_skills)]
        budget = bucket.listing_chars - sum(len(n) for n in names)
        per = [budget // len(names) + (1 if i < budget % len(names) else 0) for i in range(len(names))]
        for i, (n, dlen) in enumerate(zip(names, per)):
            topic = n.removeprefix("notes-").replace("-", " ")
            head = f"Background notes about {topic} in this environment. "
            description = (head + _sentence_filler(max(0, dlen - len(head)), seed=i * 7))[:dlen]
            d = out_dir / "skills" / n
            d.mkdir(parents=True, exist_ok=True)
            body = neutral_text(bucket.body_chars, offset=i)
            (d / "SKILL.md").write_text(f"---\nname: {n}\ndescription: {json.dumps(description)}\n---\n\n{body}\n")
            listing += len(n) + len(description)
    return {"bucket": bucket.__dict__, "plugin_name": name, "listing_chars": listing,
            "hook_chars": bucket.hook_chars, "total_chars": listing + bucket.hook_chars}


def assign_buckets(lengths: dict[str, float], tolerance: float = 0.10) -> list[list[str]]:
    """Deterministic bucketing (METHOD.md 4.1): sort by always-on length, then add each skill to the
    current bucket if the bucket's new mean (the placebo length) stays within +-tolerance of every
    member; otherwise start a new bucket. Ties broken by name."""
    buckets: list[list[str]] = []
    for name in sorted(lengths, key=lambda k: (lengths[k], k)):
        if buckets:
            cand = buckets[-1] + [name]
            mean = sum(lengths[m] for m in cand) / len(cand)
            # The placebo gets the bucket mean; it must be within +-tolerance of every member.
            if all(abs(mean / lengths[m] - 1) <= tolerance for m in cand):
                buckets[-1] = cand
                continue
        buckets.append([name])
    return buckets
