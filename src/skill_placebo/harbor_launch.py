"""`harbor` with one addition (METHOD.md amendment 9): right before the verifier starts, the agent's
container is committed to a local image, so that a verifier timeout can be re-verified once on
exactly the state the agent left. The commit happens outside the agent's and the verifier's
timeouts. Everything else is the installed Harbor CLI, unchanged.

  python -m skill_placebo.harbor_launch run -p <task> ...   (same arguments as `harbor run`)

The hook writes <trial>/snapshot.json: {"image": tag, "container": id, "seconds": s} or {"error": ...},
and, before the commit, <trial>/diff.json with the size of the agent's final diff (amendment 12).
Only the file system is captured: processes the agent left running are not part of the image.
"""
from __future__ import annotations

import asyncio
import json
import sys
import time
from pathlib import Path

SNAPSHOT_REPO = "skill-placebo-snapshot"


def project_name(trial_name: str) -> str:
    """The docker compose project Harbor 0.23.0 uses for a trial's agent environment."""
    from harbor.environments.docker.docker import _sanitize_docker_compose_project_name

    return _sanitize_docker_compose_project_name(f"{trial_name}__env")


def snapshot_tag(trial_name: str) -> str:
    return f"{SNAPSHOT_REPO}:{project_name(trial_name)}"[:128]


async def _docker(*args: str, timeout: float) -> str:
    p = await asyncio.create_subprocess_exec("docker", *args, stdout=asyncio.subprocess.PIPE,
                                             stderr=asyncio.subprocess.STDOUT)
    out, _ = await asyncio.wait_for(p.communicate(), timeout=timeout)
    if p.returncode:
        raise RuntimeError(f"docker {args[0]} rc={p.returncode}: {out.decode(errors='replace')[-300:]}")
    return out.decode(errors="replace")


async def _record_diff(container: str, ev, trial_dir: Path) -> None:
    """Amendment 12: the agent's final diff, read-only, before the snapshot and the verifier.
    Writes <trial>/diff.json; any failure is recorded there and the trial goes on."""
    from skill_placebo.diffmeasure import measure

    t0 = time.time()
    try:
        task_dir = getattr(getattr(ev.config, "task", None), "path", None)
        rec = await measure(container, Path(task_dir) if task_dir else None)
    except Exception as e:  # noqa: BLE001
        rec = {"error": f"{type(e).__name__}: {e}"}
    rec["seconds"] = round(time.time() - t0, 1)
    try:
        trial_dir.mkdir(parents=True, exist_ok=True)
        (trial_dir / "diff.json").write_text(json.dumps(rec) + "\n")
    except OSError:
        pass


async def snapshot_hook(ev) -> None:
    """VERIFICATION_START hook. Never raises: a failed snapshot only means no rerun is possible."""
    trial_dir = Path(ev.config.trials_dir) / ev.config.trial_name
    rec: dict = {"project": project_name(ev.config.trial_name)}
    t0 = time.time()
    try:
        ids = (await _docker("ps", "-q", "--filter", f"label=com.docker.compose.project={rec['project']}",
                             "--filter", "label=com.docker.compose.service=main", timeout=60)).split()
        if len(ids) != 1:
            raise RuntimeError(f"expected one main container, found {ids}")
        await _record_diff(ids[0], ev, trial_dir)
        tag = snapshot_tag(ev.config.trial_name)
        # A commit copies the container's compose labels, and Harbor's `compose down --rmi local`
        # removes every image labelled with the trial's project: relabel so the snapshot survives.
        await _docker("commit", "--change", f"LABEL com.docker.compose.project={SNAPSHOT_REPO}",
                      ids[0], tag, timeout=900)
        rec.update(image=tag, container=ids[0])
    except Exception as e:  # noqa: BLE001 - the trial must go on
        rec["error"] = f"{type(e).__name__}: {e}"
    rec["seconds"] = round(time.time() - t0, 1)
    try:
        trial_dir.mkdir(parents=True, exist_ok=True)
        (trial_dir / "snapshot.json").write_text(json.dumps(rec) + "\n")
    except OSError:
        pass


def install() -> None:
    from harbor.job import Job
    from harbor.trial.hooks import TrialEvent

    if getattr(Job, "_skill_placebo_snapshot", False):
        return
    orig = Job.__init__

    def init(self, *a, **k):
        orig(self, *a, **k)
        self.add_hook(TrialEvent.VERIFICATION_START, snapshot_hook)

    Job.__init__ = init
    Job._skill_placebo_snapshot = True


def main() -> None:
    install()
    from harbor.cli.main import app

    sys.argv[0] = "harbor"
    app()


if __name__ == "__main__":
    main()
