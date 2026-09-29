#!/usr/bin/env python3
"""Vendor the candidate task pool at pinned upstream commits into tasks/pool/ (METHOD.md section 6).

Sources and commits come from Harbor 0.23.0 registry.json (swebench-verified@1.0,
openthoughts-tblite@2.0) and harbor-framework/terminal-bench-2-1 main on 2026-09-25.

Patches applied, identical for every arm (recorded in tasks/pool/PATCHES.md):
  1. SWE-bench: FROM the amd64 swebench image -> Epoch's arm64 build of the same instance, pinned
     by manifest digest, so the pool runs natively on the arm64 runner.
  2. Terminal-Bench 2.1: the prebuilt amd64-only `docker_image` is dropped, so Harbor builds the
     task's own Dockerfile for the runner's platform (arm64 here, amd64 on a Linux x86 host).
  3. Agent timeout: min(upstream, AGENT_TIMEOUT_CAP) seconds.
  4. SWE-bench: the grading script's own dependencies (a uv script: python>=3.11, swebench==4.0.3,
     datasets==2.16.1, fastcore<1.11) are installed into the image's uv cache at build time, so that
     grading does not download a Python and packages after the agent has finished. Tests unchanged.
Nothing else in instruction, tests or solution is touched.
"""
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POOL = ROOT / "tasks" / "pool"
AGENT_TIMEOUT_CAP = 1200

SOURCES = {
    "swebench-verified": {
        "git": "https://github.com/laude-institute/harbor-datasets.git",
        "commit": "86723674f04e4209ac479d0fb75d9d9f44b4377e",
        "prefix": "datasets/swebench-verified/",
        "tasks": [
            "django__django-10973", "django__django-13401", "django__django-13925",
            "django__django-14376", "django__django-14404", "django__django-14534",
            "django__django-14725", "django__django-16454", "django__django-16950",
            "sympy__sympy-13031", "sympy__sympy-14976", "sympy__sympy-18211",
            "pytest-dev__pytest-7490", "mwaskom__seaborn-3069",
            # Harder additions for Opus 5.5 (docs/research/2026-09-28-harder-tasks.md): 2/6 and 1/6
            # on the frontier panel, tests that match their issue text.
            "django__django-11265", "django__django-15957", "django__django-11885",
            "django__django-15563", "django__django-15973", "pylint-dev__pylint-7080",
        ],
    },
    "terminal-bench-2-1": {
        "git": "https://github.com/harbor-framework/terminal-bench-2-1.git",
        "commit": "7131e4375048a0e408a8fb404b5f499d726b695b",
        "prefix": "tasks/",
        "tasks": [
            "cancel-async-tasks", "extract-elf", "openssl-selfsigned-cert", "sanitize-git-repo",
            "sqlite-with-gcov", "largest-eigenval", "sparql-university", "financial-document-processor",
            # Harder additions (docs/research/2026-09-28-harder-tasks.md)
            "query-optimize", "write-compressor", "headless-terminal", "adaptive-rejection-sampler",
        ],
    },
    "openthoughts-tblite": {
        "git": "https://github.com/open-thoughts/OpenThoughts-TBLite.git",
        "commit": "f075e463472c7790b85793b392dff1fff20cc0e3",
        "prefix": "",
        "tasks": [
            "todos-api", "api-endpoint-permission-canonicalizer", "build-merkle-tree-cli-sha512",
            "fix_async_worker_queue", "pandas-etl", "python-api-rate-limit",
            "build-system-task-ordering", "application-debug",
        ],
    },
}


# Same PEP 723 header as the parser.py that every SWE-bench test.sh writes and runs with `uv run`.
WARM_VERIFIER = (
    "# skill-placebo: pre-install the grading script's dependencies (identical in every arm)\n"
    "RUN printf '# /// script\\n# requires-python = \">=3.11\"\\n"
    "# dependencies = [\"swebench==4.0.3\", \"datasets==2.16.1\", \"fastcore<1.11\"]\\n# ///\\n"
    "import swebench, datasets\\n' > /tmp/sp_warm.py && /root/.local/bin/uv run /tmp/sp_warm.py && rm /tmp/sp_warm.py"
)


def sh(*cmd, cwd=None):
    return subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True).stdout


def epoch_digest(instance: str) -> str:
    ref = f"ghcr.io/epoch-research/swe-bench.eval.arm64.{instance}:latest"
    out = sh("docker", "buildx", "imagetools", "inspect", ref, "--format", "{{json .Manifest}}")
    return f"ghcr.io/epoch-research/swe-bench.eval.arm64.{instance}@{json.loads(out)['digest']}"


def patch_timeout(toml: Path) -> str | None:
    text = toml.read_text()
    m = re.search(r"(\[agent\][^\[]*?timeout_sec\s*=\s*)([0-9.]+)", text, re.S)
    if not m:
        return None
    old = float(m.group(2))
    if old <= AGENT_TIMEOUT_CAP:
        return None
    toml.write_text(text[: m.start(2)] + f"{AGENT_TIMEOUT_CAP:.1f}" + text[m.end(2):])
    return f"agent timeout {old:g} -> {AGENT_TIMEOUT_CAP}"


# Harder candidates for Opus 5.5 (docs/research/2026-09-29-harder-tasks-2.md), staged outside the pool
# until an amendment admits them (METHOD.md section 6).
EXTRA_SOURCES = {
    "swebench-verified": {
        **SOURCES["swebench-verified"],
        "tasks": ["django__django-13512", "django__django-14140", "django__django-11141", "sphinx-doc__sphinx-10435",
                  "django__django-16256", "sympy__sympy-17630", "django__django-11734"],
    },
    "terminal-bench-2-1": {
        **SOURCES["terminal-bench-2-1"],
        "tasks": ["make-doom-for-mips", "video-processing"],
    },
}


def main():
    global POOL, SOURCES
    if "--extra" in sys.argv:
        POOL, SOURCES = ROOT / "tasks" / "pool-extra", EXTRA_SOURCES
    POOL.mkdir(parents=True, exist_ok=True)
    manifest = {"sources": {}, "tasks": []}
    patches = [(ROOT / "tasks" / "PATCHES_HEADER.md").read_text().rstrip("\n"), "", f"Agent timeout cap: {AGENT_TIMEOUT_CAP} s.", ""]
    for src, cfg in SOURCES.items():
        manifest["sources"][src] = {k: cfg[k] for k in ("git", "commit")}
        with tempfile.TemporaryDirectory() as tmp:
            sh("git", "init", "-q", tmp)
            sh("git", "remote", "add", "origin", cfg["git"], cwd=tmp)
            sh("git", "sparse-checkout", "set", "--no-cone", *[f"/{cfg['prefix']}{t}/" for t in cfg["tasks"]], cwd=tmp)
            sh("git", "fetch", "-q", "--depth", "1", "--filter=blob:none", "origin", cfg["commit"], cwd=tmp)
            sh("git", "checkout", "-q", "FETCH_HEAD", cwd=tmp)
            for t in cfg["tasks"]:
                s = Path(tmp) / f"{cfg['prefix']}{t}"
                if not s.is_dir():
                    sys.exit(f"missing {src}/{t} at {cfg['commit']}")
                d = POOL / src / t
                if d.exists():
                    shutil.rmtree(d)
                shutil.copytree(s, d)
                notes = []
                if src == "swebench-verified":
                    df = d / "environment" / "Dockerfile"
                    text = df.read_text()
                    new_from = epoch_digest(t)
                    text2, n = re.subn(r"^FROM swebench/sweb\.eval\.x86_64\.\S+", f"FROM {new_from}", text, flags=re.M)
                    if n != 1:
                        sys.exit(f"{t}: FROM line not found")
                    text2 = text2.rstrip("\n") + "\n\n" + WARM_VERIFIER + "\n"
                    df.write_text(text2)
                    notes.append(f"FROM -> {new_from}")
                    notes.append("verifier dependencies pre-installed in the uv cache")
                if src == "terminal-bench-2-1":
                    tt = d / "task.toml"
                    text, n = re.subn(r"^docker_image\s*=.*$", "# docker_image removed by skill-placebo: build from environment/Dockerfile", tt.read_text(), flags=re.M)
                    if n:
                        tt.write_text(text)
                        notes.append("prebuilt docker_image dropped, built from Dockerfile")
                note = patch_timeout(d / "task.toml")
                if note:
                    notes.append(note)
                manifest["tasks"].append({"source": src, "name": t, "path": f"tasks/{POOL.name}/{src}/{t}", "patches": notes})
                patches.append(f"- `{src}/{t}`: " + ("; ".join(notes) if notes else "none"))
                print(f"{src}/{t}: {'; '.join(notes) or 'as is'}")
    (POOL / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")
    (POOL / "PATCHES.md").write_text("\n".join(patches) + "\n")


if __name__ == "__main__":
    main()
