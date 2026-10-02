#!/usr/bin/env python3
"""Export the published trial records from jobs/ (gitignored) into results/ (METHOD.md section 15).

  scripts/export_trials.py            # Claude Code main run + Codex pilot kill test
Layout:
  results/main/claude-code/trials/<arm>/<job>/        blocks 0-1, the primary analysis (amendment 17)
  results/main/claude-code/appendix-block2/<arm>/<job>/  valid trials of the incomplete block 2
  results/main/claude-code/not-analysed/<job>/        every other attempt, with its reason (infrastructure,
                                                      interrupted): all runs are reported (METHOD.md section 7)
  results/pilot/codex/trials/<arm>/<job>/             the Codex pilot kill test (secondary result)
Per trial: result.json, the agent's session log and ATIF trajectory, approval turns, the verifier's output
and reward, and the amendment 9/12/14 records (diff.json, snapshot.json, verifier_rerun.json). Then every
exported file is scrubbed in place (keys, the runner's home path, personal strings) and checked again.
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from skill_placebo.collect import INFRA_EXCEPTIONS  # noqa: E402

KEEP = ["result.json", "diff.json", "snapshot.json", "verifier_rerun.json", "agent/approval_turns.txt",
        "verifier/test-stdout.txt", "verifier/reward.txt", "verifier/reward.json"]
# The agent's full logs are large (base64 documents inside; ~560 MB for the Claude Code run, gzip x2), so they
# go into one archive per harness outside git (dist/, for a release asset), with a sha256 manifest in results/.
LOGS = ["agent/trajectory.json", "agent/claude-code.txt", "agent/codex.txt"]


def copy_trial(tdir: Path, dest: Path, logs_dest: Path | None = None) -> int:
    n = 0
    for rel in LOGS:
        src = tdir / rel
        if logs_dest is not None and src.exists():
            (logs_dest / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, logs_dest / rel)
    for rel in KEEP:
        src = tdir / rel
        if src.exists():
            (dest / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest / rel)
            n += 1
    for rollout in tdir.glob("agent/**/rollout-*.jsonl"):  # Codex session log
        if logs_dest is not None:
            (logs_dest / "agent").mkdir(parents=True, exist_ok=True)
            shutil.copy2(rollout, logs_dest / "agent" / rollout.name)
    return n


def attempts(jobs: Path) -> dict[str, list[Path]]:
    out: dict[str, list[Path]] = {}
    for d in sorted(jobs.glob("b*__*")):
        if d.is_dir():
            out.setdefault(d.name.split("__r")[0], []).append(d)
    return out


def exception(tdir: Path) -> str | None:
    return (json.loads((tdir / "result.json").read_text()).get("exception_info") or {}).get("exception_type")


def export(jobs: Path, out: Path, primary_blocks: int | None, logs: Path) -> dict:
    counts = {"primary": 0, "appendix": 0, "not_analysed": 0}
    for base, tries in attempts(jobs).items():
        arm = base.split("__")[2]
        block = int(base[1:3])
        last = sorted(tries, key=lambda p: (len(p.name), p.name))[-1]
        for d in tries:
            tdirs = [t for t in d.glob("*/") if (t / "result.json").exists()]
            reason = None
            if (d / "interrupted.json").exists():
                reason = "interrupted"
            elif not tdirs:
                reason = "no trial result"
            elif exception(tdirs[0]) in INFRA_EXCEPTIONS:
                reason = f"infrastructure: {exception(tdirs[0])}"
            elif d != last:
                reason = "superseded attempt"
            if reason:
                dest = out / "not-analysed" / d.name
                dest.mkdir(parents=True, exist_ok=True)
                for t in tdirs:
                    copy_trial(t, dest / t.name, logs / "not-analysed" / d.name / t.name)
                (dest / "reason.txt").write_text(reason + "\n")
                counts["not_analysed"] += 1
                continue
            where = "trials" if primary_blocks is None or block < primary_blocks else f"appendix-block{block}"
            for t in tdirs:
                copy_trial(t, out / where / arm / d.name / t.name, logs / where / arm / d.name / t.name)
            counts["primary" if where == "trials" else "appendix"] += 1
    return counts


def main():
    import hashlib
    import tarfile
    targets = [(ROOT / "jobs/main/claude-code", ROOT / "results/main/claude-code", 2, "v1-claude-code-main"),
               (ROOT / "jobs/pilot/codex/kill", ROOT / "results/pilot/codex", None, "v1-codex-pilot")]
    staging = ROOT / "dist" / "logs-staging"
    shutil.rmtree(staging, ignore_errors=True)
    exported = []
    for jobs, out, blocks, name in targets:
        for sub in ("trials", "not-analysed") + tuple(p.name for p in out.glob("appendix-block*")):
            shutil.rmtree(out / sub, ignore_errors=True)
        counts = export(jobs, out, blocks, staging / name)
        print(f"{jobs.relative_to(ROOT)} -> {out.relative_to(ROOT)}: {counts}")
        exported += [str(out), str(staging / name)]
    subprocess.run([sys.executable, str(ROOT / "scripts/scrub.py"), "--redact", *exported], check=False,
                   stdout=subprocess.DEVNULL)
    r = subprocess.run([sys.executable, str(ROOT / "scripts/scrub.py"), "--check", *exported])
    if r.returncode:
        sys.exit(r.returncode)
    for jobs, out, blocks, name in targets:  # one archive of the full agent logs per target, after the scrub
        archive = ROOT / "dist" / f"skill-placebo-{name}-agent-logs.tar.gz"
        with tarfile.open(archive, "w:gz") as tar:
            tar.add(staging / name, arcname=name)
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        (out / "AGENT_LOGS.json").write_text(json.dumps({
            "archive": archive.name, "sha256": digest, "bytes": archive.stat().st_size,
            "contents": "each trial's agent/claude-code.txt (raw stream) or Codex rollout, and agent/trajectory.json "
                        "(ATIF), under the same <where>/<arm>/<job>/<trial>/ paths as this folder; scrubbed",
            "published_as": "GitHub release asset (release v0.1.0)"}, indent=1) + "\n")
        print(f"{archive.relative_to(ROOT)}: {archive.stat().st_size / 1e6:.0f} MB, sha256 {digest[:12]}")
    shutil.rmtree(staging, ignore_errors=True)


if __name__ == "__main__":
    main()
