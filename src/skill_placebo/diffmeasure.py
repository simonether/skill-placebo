"""Size of the agent's final diff, read right before verification (METHOD.md amendment 12).

Read-only by construction: `git diff --numstat` against the task's base commit and `wc -l` over untracked
files, with GIT_OPTIONAL_LOCKS=0 so git never rewrites the index (the verifier applies its test patch to
this repository afterwards). SWE-bench tasks only (a git repository at /testbed); for other tasks,
`docker diff` is recorded as an exploratory list of changed paths. Nothing here raises: an error goes
into the record and the trial goes on.
"""
from __future__ import annotations

import asyncio
import re
from pathlib import Path

SWE_REPO = "/testbed"
# docker diff paths that belong to the agent's installation or to caches, not to the task's work.
NOISE = ("/tmp", "/root/.cache", "/root/.npm", "/root/.local", "/root/.claude", "/root/.config", "/root/.nvm",
         "/root/.codex", "/root/.bashrc", "/root/.profile", "/logs", "/proc", "/dev", "/run", "/var/cache",
         "/var/lib/apt", "/var/lib/dpkg", "/var/log", "/usr", "/etc", "/opt/plugins", "/root/.agents", "/installed-agent")


async def _run(*args: str, timeout: float = 120) -> tuple[int, str]:
    p = await asyncio.create_subprocess_exec(*args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
    out, _ = await asyncio.wait_for(p.communicate(), timeout=timeout)
    return p.returncode, out.decode(errors="replace")


def base_commit(task_dir: Path | None) -> str | None:
    """The commit a SWE-bench verifier checks out (first `git checkout <sha>` in tests/test.sh)."""
    if task_dir is None or not (Path(task_dir) / "tests" / "test.sh").exists():
        return None
    m = re.search(r"git checkout ([0-9a-f]{40})", (Path(task_dir) / "tests" / "test.sh").read_text())
    return m.group(1) if m else None


def parse_numstat(text: str) -> dict:
    added = deleted = files = binary = 0
    for line in text.splitlines():
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        files += 1
        if parts[0] == "-" or parts[1] == "-":
            binary += 1
            continue
        added += int(parts[0])
        deleted += int(parts[1])
    return {"tracked_added": added, "tracked_deleted": deleted, "tracked_files": files, "tracked_binary": binary}


def parse_wc(text: str) -> dict:
    lines = files = 0
    for line in text.splitlines():
        m = re.match(r"\s*(\d+)\s+(.+)$", line)
        if not m or m.group(2) == "total":
            continue
        files += 1
        lines += int(m.group(1))
    return {"untracked_lines": lines, "untracked_files": files}


def parse_docker_diff(text: str) -> dict:
    kinds = {"A": 0, "C": 0, "D": 0}
    tops: dict[str, int] = {}
    for line in text.splitlines():
        m = re.match(r"([ACD]) (/.*)$", line.strip())
        if not m:
            continue
        kind, path = m.groups()
        if any(path == n or path.startswith(n + "/") for n in NOISE):
            continue
        kinds[kind] += 1
        top = "/".join(path.split("/")[:3])
        tops[top] = tops.get(top, 0) + 1
    return {"docker_diff": kinds, "docker_diff_top": dict(sorted(tops.items(), key=lambda kv: -kv[1])[:10])}


async def measure(container: str, task_dir: Path | None) -> dict:
    rec: dict = {"method": None}
    try:
        base = base_commit(task_dir)
        rc, _ = await _run("docker", "exec", container, "test", "-d", f"{SWE_REPO}/.git", timeout=30)
        if rc == 0 and base:
            git = ["docker", "exec", "-e", "GIT_OPTIONAL_LOCKS=0", "-w", SWE_REPO, container,
                   "git", "-c", "safe.directory=*", "-c", "core.fileMode=false"]
            rc1, numstat = await _run(*git, "diff", "--no-ext-diff", "--no-renames", "--numstat", base)
            rc2, head = await _run(*git, "rev-parse", "HEAD")
            rc3, wc = await _run("docker", "exec", "-e", "GIT_OPTIONAL_LOCKS=0", "-w", SWE_REPO, container, "sh", "-c",
                                 "git -c safe.directory='*' ls-files --others --exclude-standard -z | xargs -0 -r wc -l --")
            if rc1 or rc2 or rc3:
                raise RuntimeError(f"git rc={rc1},{rc2},{rc3}: {(numstat + wc)[-300:]}")
            rec.update(method="git (amendment 12a)", base=base, head=head.strip(), **parse_numstat(numstat), **parse_wc(wc))
            rec["lines_changed"] = rec["tracked_added"] + rec["tracked_deleted"] + rec["untracked_lines"]
        else:
            rc, out = await _run("docker", "diff", container, timeout=300)
            if rc:
                raise RuntimeError(f"docker diff rc={rc}: {out[-300:]}")
            rec.update(method="docker diff (exploratory)", **parse_docker_diff(out))
    except Exception as e:  # noqa: BLE001 - never fail the trial
        rec["error"] = f"{type(e).__name__}: {e}"
    return rec
