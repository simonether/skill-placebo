#!/usr/bin/env python3
"""Check out every skill in skills.lock.json at its pinned commit into vendor/<id>/ (gitignored).

vendor/ is not committed: some repos have no license file, and the pinned sha is enough to reproduce.
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "vendor"


def sh(*cmd, cwd=None):
    subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True)


def main(ids=None):
    lock = json.loads((ROOT / "skills.lock.json").read_text())
    VENDOR.mkdir(exist_ok=True)
    for s in lock["skills"]:
        if ids and s["id"] not in ids:
            continue
        d = VENDOR / s["id"]
        if (d / ".git").exists():
            head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=d, capture_output=True, text=True).stdout.strip()
            if head == s["sha"]:
                print(f"{s['id']}: ok {head[:7]}")
                continue
            shutil.rmtree(d)
        d.mkdir(parents=True)
        sh("git", "init", "-q", cwd=d)
        sh("git", "remote", "add", "origin", f"https://github.com/{s['repo']}.git", cwd=d)
        sh("git", "fetch", "-q", "--depth", "1", "origin", s["sha"], cwd=d)
        sh("git", "checkout", "-q", "FETCH_HEAD", cwd=d)
        print(f"{s['id']}: {s['repo']}@{s['sha'][:7]}")


if __name__ == "__main__":
    main(sys.argv[1:] or None)
