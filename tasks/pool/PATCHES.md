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

- `swebench-verified/django__django-10973`: FROM -> ghcr.io/epoch-research/swe-bench.eval.arm64.django__django-10973@sha256:d745b55cd7ba4c77dc67a3b2eb5007e2d1e4ddb609e3e861bac2621e84c335b2; verifier dependencies pre-installed in the uv cache; agent timeout 3000 -> 1200
- `swebench-verified/django__django-13401`: FROM -> ghcr.io/epoch-research/swe-bench.eval.arm64.django__django-13401@sha256:26307abc1ba36b062ecfd8ba0357e3bbfcfb0e1264b9f7ef776bd10c75650608; verifier dependencies pre-installed in the uv cache; agent timeout 3000 -> 1200
- `swebench-verified/django__django-13925`: FROM -> ghcr.io/epoch-research/swe-bench.eval.arm64.django__django-13925@sha256:8d223353a1542e377f4bf5695c42fcd2a2fe7bb7e78c8c88eab191bc297a9598; verifier dependencies pre-installed in the uv cache; agent timeout 3000 -> 1200
- `swebench-verified/django__django-14376`: FROM -> ghcr.io/epoch-research/swe-bench.eval.arm64.django__django-14376@sha256:a4d53c909207df34e06b1a8a5916a49bd25fe1605c7d32393517f12e90f5e6a7; verifier dependencies pre-installed in the uv cache; agent timeout 3000 -> 1200
- `swebench-verified/django__django-14404`: FROM -> ghcr.io/epoch-research/swe-bench.eval.arm64.django__django-14404@sha256:a710bbf5156359b8ce72f505362ffbc03b7d89bc82b2d1a0acb1987bef6cc8ee; verifier dependencies pre-installed in the uv cache; agent timeout 3000 -> 1200
- `swebench-verified/django__django-14534`: FROM -> ghcr.io/epoch-research/swe-bench.eval.arm64.django__django-14534@sha256:0a9abe8bd0663ff2eafbc612421baaa0d02d9d6ece0f895d20e1e444b00ef3eb; verifier dependencies pre-installed in the uv cache; agent timeout 3000 -> 1200
- `swebench-verified/django__django-14725`: FROM -> ghcr.io/epoch-research/swe-bench.eval.arm64.django__django-14725@sha256:90cb826e1a7072f3b3b5b5d48c979564f8a9fb3622888ce2268350aa3239386d; verifier dependencies pre-installed in the uv cache; agent timeout 3000 -> 1200
- `swebench-verified/django__django-16454`: FROM -> ghcr.io/epoch-research/swe-bench.eval.arm64.django__django-16454@sha256:f229e82282009f10dee564650c016e8b05a8033a3a6c16553e6d047b0fdfcb1e; verifier dependencies pre-installed in the uv cache; agent timeout 3000 -> 1200
- `swebench-verified/django__django-16950`: FROM -> ghcr.io/epoch-research/swe-bench.eval.arm64.django__django-16950@sha256:dec9c44aa5ef52a811531732a62001ea28fe794f09bfd9f81c74e3bd77beb1cf; verifier dependencies pre-installed in the uv cache; agent timeout 3000 -> 1200
- `swebench-verified/sympy__sympy-13031`: FROM -> ghcr.io/epoch-research/swe-bench.eval.arm64.sympy__sympy-13031@sha256:62b9003c0297529ee26425638af9ae8c406514d1c409f415cb9d51f71d680edb; verifier dependencies pre-installed in the uv cache; agent timeout 3000 -> 1200
- `swebench-verified/sympy__sympy-14976`: FROM -> ghcr.io/epoch-research/swe-bench.eval.arm64.sympy__sympy-14976@sha256:077064ba433b9b9d1eaa0f95b10bf37170d3e065eb6e2be82edaf604b141d62f; verifier dependencies pre-installed in the uv cache; agent timeout 3000 -> 1200
- `swebench-verified/sympy__sympy-18211`: FROM -> ghcr.io/epoch-research/swe-bench.eval.arm64.sympy__sympy-18211@sha256:459e5daffe0a9b8c7513f272afc42ce58e8dc87e253e8b363cbcfcc00d92ea75; verifier dependencies pre-installed in the uv cache; agent timeout 3000 -> 1200
- `swebench-verified/pytest-dev__pytest-7490`: FROM -> ghcr.io/epoch-research/swe-bench.eval.arm64.pytest-dev__pytest-7490@sha256:f049336c9c8201e8c61280685655078ee5fdd2c8e087c9830816af9e54e92fe9; verifier dependencies pre-installed in the uv cache; agent timeout 3000 -> 1200
- `swebench-verified/mwaskom__seaborn-3069`: FROM -> ghcr.io/epoch-research/swe-bench.eval.arm64.mwaskom__seaborn-3069@sha256:d69b41f4a45e52de029b569c7fd7be022b1e9727cb810ca84907908b65c86510; verifier dependencies pre-installed in the uv cache; agent timeout 3000 -> 1200
- `swebench-verified/django__django-11265`: FROM -> ghcr.io/epoch-research/swe-bench.eval.arm64.django__django-11265@sha256:5ec766194c8370a04d2adcf57e2f5df870a2085f5f438017acae64779d63e6c7; verifier dependencies pre-installed in the uv cache; agent timeout 3000 -> 1200
- `swebench-verified/django__django-15957`: FROM -> ghcr.io/epoch-research/swe-bench.eval.arm64.django__django-15957@sha256:2b7839f529cdbf38b2748987841670e17d7a449ebaaacc11567d22d5ccf1f4e3; verifier dependencies pre-installed in the uv cache; agent timeout 3000 -> 1200
- `swebench-verified/django__django-11885`: FROM -> ghcr.io/epoch-research/swe-bench.eval.arm64.django__django-11885@sha256:f88911185c2911801e98aa00ac1e348044a4141cd29fc738c0acf0458f037769; verifier dependencies pre-installed in the uv cache; agent timeout 3000 -> 1200
- `swebench-verified/django__django-15563`: FROM -> ghcr.io/epoch-research/swe-bench.eval.arm64.django__django-15563@sha256:75079c5da14982bbcdfef420ab8960e8bb4c3e071763fb4ba86580caf4f34b5d; verifier dependencies pre-installed in the uv cache; agent timeout 3000 -> 1200
- `swebench-verified/django__django-15973`: FROM -> ghcr.io/epoch-research/swe-bench.eval.arm64.django__django-15973@sha256:f4349ec85f109b64f780d09807744e5c01d06c276cca2013620ad1a819b6775e; verifier dependencies pre-installed in the uv cache; agent timeout 3000 -> 1200
- `swebench-verified/pylint-dev__pylint-7080`: FROM -> ghcr.io/epoch-research/swe-bench.eval.arm64.pylint-dev__pylint-7080@sha256:a953de0a577f860c32ab4c544ee357c9b008bb6bd31b08207f54077b0b8d385f; verifier dependencies pre-installed in the uv cache; agent timeout 3000 -> 1200
- `terminal-bench-2-1/cancel-async-tasks`: prebuilt docker_image dropped, built from Dockerfile
- `terminal-bench-2-1/extract-elf`: prebuilt docker_image dropped, built from Dockerfile
- `terminal-bench-2-1/openssl-selfsigned-cert`: prebuilt docker_image dropped, built from Dockerfile
- `terminal-bench-2-1/sanitize-git-repo`: prebuilt docker_image dropped, built from Dockerfile
- `terminal-bench-2-1/sqlite-with-gcov`: prebuilt docker_image dropped, built from Dockerfile
- `terminal-bench-2-1/largest-eigenval`: prebuilt docker_image dropped, built from Dockerfile
- `terminal-bench-2-1/sparql-university`: prebuilt docker_image dropped, built from Dockerfile
- `terminal-bench-2-1/financial-document-processor`: prebuilt docker_image dropped, built from Dockerfile
- `terminal-bench-2-1/query-optimize`: prebuilt docker_image dropped, built from Dockerfile
- `terminal-bench-2-1/write-compressor`: prebuilt docker_image dropped, built from Dockerfile
- `terminal-bench-2-1/headless-terminal`: prebuilt docker_image dropped, built from Dockerfile
- `terminal-bench-2-1/adaptive-rejection-sampler`: prebuilt docker_image dropped, built from Dockerfile
- `openthoughts-tblite/todos-api`: none
- `openthoughts-tblite/api-endpoint-permission-canonicalizer`: none
- `openthoughts-tblite/build-merkle-tree-cli-sha512`: none
- `openthoughts-tblite/fix_async_worker_queue`: none
- `openthoughts-tblite/pandas-etl`: none
- `openthoughts-tblite/python-api-rate-limit`: none
- `openthoughts-tblite/build-system-task-ordering`: none
- `openthoughts-tblite/application-debug`: none

Added 2026-09-29 (amendment 6):

- `swebench-verified/django__django-13512`: FROM -> ghcr.io/epoch-research/swe-bench.eval.arm64.django__django-13512@sha256:6a272aafc118cce5a8cf69a799a68a4466e6621d583ae160a00929fc332aed30; verifier dependencies pre-installed in the uv cache; agent timeout 3000 -> 1200
- `swebench-verified/django__django-14140`: FROM -> ghcr.io/epoch-research/swe-bench.eval.arm64.django__django-14140@sha256:1578851fcc2acd92b9f942c13f70d54ee696b64335fa4a82ab8c7cfd56fe6315; verifier dependencies pre-installed in the uv cache; agent timeout 3000 -> 1200
- `swebench-verified/django__django-11141`: FROM -> ghcr.io/epoch-research/swe-bench.eval.arm64.django__django-11141@sha256:0986d26e380dedb0c9b7515b9a3d734dc1754604d4d744886cd0e9ddfc0a53d5; verifier dependencies pre-installed in the uv cache; agent timeout 3000 -> 1200
- `swebench-verified/sphinx-doc__sphinx-10435`: FROM -> ghcr.io/epoch-research/swe-bench.eval.arm64.sphinx-doc__sphinx-10435@sha256:c402b674b9ad20fe157b63be3ba86b4ddb98850ec044e75fbcedca9ee252a87c; verifier dependencies pre-installed in the uv cache; agent timeout 3000 -> 1200
- `swebench-verified/django__django-16256`: FROM -> ghcr.io/epoch-research/swe-bench.eval.arm64.django__django-16256@sha256:4015ab52b068f071ec268f4914bdb3301edc6c170485263a107afbe4d07bb88b; verifier dependencies pre-installed in the uv cache; agent timeout 3000 -> 1200
- `swebench-verified/sympy__sympy-17630`: FROM -> ghcr.io/epoch-research/swe-bench.eval.arm64.sympy__sympy-17630@sha256:8a73a34820b271dea84bccdc0874709b180b08d040fed7be938c32db92cfb650; verifier dependencies pre-installed in the uv cache; agent timeout 3000 -> 1200
- `swebench-verified/django__django-11734`: FROM -> ghcr.io/epoch-research/swe-bench.eval.arm64.django__django-11734@sha256:6acc328f952f95c2bfcb0dcc3dedd024923e8e4c343851c3b1d686f5f1753aee; verifier dependencies pre-installed in the uv cache; agent timeout 3000 -> 1200
- `terminal-bench-2-1/video-processing`: prebuilt docker_image dropped, built from Dockerfile; agent timeout 3600 -> 1200
