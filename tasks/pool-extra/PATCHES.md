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

Agent timeout cap: 1200 s.

- `swebench-verified/django__django-13512`: FROM -> ghcr.io/epoch-research/swe-bench.eval.arm64.django__django-13512@sha256:6a272aafc118cce5a8cf69a799a68a4466e6621d583ae160a00929fc332aed30; verifier dependencies pre-installed in the uv cache; agent timeout 3000 -> 1200
- `swebench-verified/django__django-14140`: FROM -> ghcr.io/epoch-research/swe-bench.eval.arm64.django__django-14140@sha256:1578851fcc2acd92b9f942c13f70d54ee696b64335fa4a82ab8c7cfd56fe6315; verifier dependencies pre-installed in the uv cache; agent timeout 3000 -> 1200
- `swebench-verified/django__django-11141`: FROM -> ghcr.io/epoch-research/swe-bench.eval.arm64.django__django-11141@sha256:0986d26e380dedb0c9b7515b9a3d734dc1754604d4d744886cd0e9ddfc0a53d5; verifier dependencies pre-installed in the uv cache; agent timeout 3000 -> 1200
- `swebench-verified/sphinx-doc__sphinx-10435`: FROM -> ghcr.io/epoch-research/swe-bench.eval.arm64.sphinx-doc__sphinx-10435@sha256:c402b674b9ad20fe157b63be3ba86b4ddb98850ec044e75fbcedca9ee252a87c; verifier dependencies pre-installed in the uv cache; agent timeout 3000 -> 1200
- `swebench-verified/django__django-16256`: FROM -> ghcr.io/epoch-research/swe-bench.eval.arm64.django__django-16256@sha256:4015ab52b068f071ec268f4914bdb3301edc6c170485263a107afbe4d07bb88b; verifier dependencies pre-installed in the uv cache; agent timeout 3000 -> 1200
- `swebench-verified/sympy__sympy-17630`: FROM -> ghcr.io/epoch-research/swe-bench.eval.arm64.sympy__sympy-17630@sha256:8a73a34820b271dea84bccdc0874709b180b08d040fed7be938c32db92cfb650; verifier dependencies pre-installed in the uv cache; agent timeout 3000 -> 1200
- `swebench-verified/django__django-11734`: FROM -> ghcr.io/epoch-research/swe-bench.eval.arm64.django__django-11734@sha256:6acc328f952f95c2bfcb0dcc3dedd024923e8e4c343851c3b1d686f5f1753aee; verifier dependencies pre-installed in the uv cache; agent timeout 3000 -> 1200
- `terminal-bench-2-1/make-doom-for-mips`: prebuilt docker_image dropped, built from Dockerfile
- `terminal-bench-2-1/video-processing`: prebuilt docker_image dropped, built from Dockerfile; agent timeout 3600 -> 1200
