# Patches to vendored tasks

Every patch below is applied identically to every arm of every harness. None touches a task's
instruction, tests or reference solution. Their only effect is on the environment the task runs and
is graded in, so they cannot favour one arm over another.

| Patch | Where | Why | Effect on fairness |
|---|---|---|---|
| Base image → Epoch's arm64 build of the same SWE-bench instance, pinned by digest | SWE-bench Dockerfiles | the runner is arm64; the upstream images are amd64-only and would run under emulation | none: same repository state and conda env; same for all arms |
| Prebuilt `docker_image` dropped, task built from its own Dockerfile | Terminal-Bench 2.1 task.toml | the prebuilt images are amd64-only | none: the same Dockerfile the image was built from; same for all arms |
| Agent timeout = min(upstream, 1200 s) | task.toml | keeps the run window and subscription use bounded | none for comparisons: the same cap in every arm; a timeout is a failed trial in every arm |
| Grading script's dependencies pre-installed into the image's uv cache | SWE-bench Dockerfiles | the unpatched grader downloads a Python and swebench/datasets/fastcore after the agent has finished; a network stall hung one oracle grading for 20 minutes, which in a real trial would throw away the agent's finished work | none: the grader runs the same script with the same pinned versions; only where its dependencies come from changes |
| Base images python:3.13-slim-bookworm, python:3.11-slim, ubuntu:24.04 pulled from Docker Hub's official mirror `mirror.gcr.io` and tagged locally | local Docker, not the task files | Docker Hub throttled anonymous pulls (HTTP 429) | none: same images (digests in BASE_IMAGES.txt); same for all arms |

Per-task list:

