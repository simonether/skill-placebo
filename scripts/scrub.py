#!/usr/bin/env python3
"""Find and redact secrets and personal paths in run artifacts before they are published.

Usage:
  scripts/scrub.py --check PATH...    exit 1 if anything sensitive is found (prints file:line, never the value)
  scripts/scrub.py --redact PATH...   rewrite text files in place with [REDACTED:<kind>]

Detects: exact values of every KEY=VALUE in .secrets/api.env and of every token in
.secrets/codex-home/auth.json (the most reliable check),
Anthropic / OpenRouter / OpenAI / GitHub key shapes, bearer tokens, the runner's own home directory
(not other people's paths quoted in public task texts) and the owner's e-mail. Binary files are reported, not rewritten.
"""
import argparse
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECRETS_ENV = os.path.join(ROOT, ".secrets", "api.env")
CODEX_AUTH = os.path.join(ROOT, ".secrets", "codex-home", "auth.json")

PATTERNS = [
    ("anthropic-key", re.compile(r"sk-ant-[A-Za-z0-9_\-]{20,}")),
    ("openrouter-key", re.compile(r"sk-or-v1-[A-Za-z0-9]{20,}")),
    ("openai-key", re.compile(r"sk-(?!ant-|or-)(?:proj-)?[A-Za-z0-9_\-]{32,}")),
    ("github-token", re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{30,}\b|github_pat_[A-Za-z0-9_]{40,}")),
    ("bearer", re.compile(r"(?i)bearer\s+[A-Za-z0-9._\-]{24,}")),
    ("home-path", re.compile(re.escape(os.path.expanduser("~")) + r"(?![A-Za-z0-9._\-])")),
    ("email", re.compile(r"owner@example\.invalid", re.I)),
]


def secret_values():
    vals = []
    try:
        with open(SECRETS_ENV, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                name, v = line.split("=", 1)
                v = v.strip().strip('"').strip("'")
                if len(v) >= 12:
                    vals.append((name.strip(), v))
    except FileNotFoundError:
        pass
    # Every long string in the dedicated Codex login (access/refresh/id tokens, account id).
    try:
        import json

        def walk(o, key=""):
            if isinstance(o, dict):
                for k, v in o.items():
                    walk(v, k)
            elif isinstance(o, list):
                for v in o:
                    walk(v, key)
            elif isinstance(o, str) and len(o) >= 20 and ("token" in key or key in ("account_id", "OPENAI_API_KEY")):
                vals.append((f"codex-auth:{key}", o))

        with open(CODEX_AUTH, encoding="utf-8") as f:
            walk(json.load(f))
    except (FileNotFoundError, ValueError):
        pass
    return vals


def iter_files(paths):
    for p in paths:
        if os.path.isfile(p):
            yield p
        for dirpath, dirnames, filenames in os.walk(p):
            dirnames[:] = [d for d in dirnames if d not in (".git", ".venv", "node_modules")]
            for fn in filenames:
                yield os.path.join(dirpath, fn)


def scan_text(text, values):
    """Yield (kind, start, end) for every sensitive span."""
    for name, v in values:
        for m in re.finditer(re.escape(v), text):
            yield f"secret:{name}", m.start(), m.end()
    for kind, rx in PATTERNS:
        for m in rx.finditer(text):
            yield kind, m.start(), m.end()


def main():
    ap = argparse.ArgumentParser()
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--redact", action="store_true")
    ap.add_argument("paths", nargs="+")
    args = ap.parse_args()
    values = secret_values()
    found = 0
    for path in iter_files(args.paths):
        try:
            raw = open(path, "rb").read()
        except OSError:
            continue
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            hits = [k for k, v in values if v.encode() in raw]
            if hits:
                found += 1
                print(f"{path}: binary file contains {', '.join('secret:' + h for h in hits)}")
            continue
        spans = sorted(set(scan_text(text, values)), key=lambda s: (s[1], -(s[2] - s[1]), s[0]))
        if not spans:
            continue
        found += len(spans)
        for kind, s, _ in spans:
            line = text.count("\n", 0, s) + 1
            print(f"{path}:{line}: {kind}")
        if args.redact:
            out, last = [], 0
            for kind, s, e in spans:
                if s < last:
                    continue
                out.append(text[last:s])
                out.append("~" if kind == "home-path" else f"[REDACTED:{kind}]")
                last = e
            out.append(text[last:])
            with open(path, "w", encoding="utf-8") as f:
                f.write("".join(out))
    if args.check and found:
        print(f"scrub: {found} sensitive spans found", file=sys.stderr)
        sys.exit(1)
    print(f"scrub: {'redacted' if args.redact else 'clean' if not found else 'found'} ({found} spans)", file=sys.stderr)


if __name__ == "__main__":
    main()
