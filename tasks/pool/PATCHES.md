# Patches to vendored tasks

Agent timeout cap: 1200 s.

- `swebench-verified/django__django-10973`: FROM -> ghcr.io/epoch-research/swe-bench.eval.arm64.django__django-10973@sha256:d745b55cd7ba4c77dc67a3b2eb5007e2d1e4ddb609e3e861bac2621e84c335b2; agent timeout 3000 -> 1200
- `swebench-verified/django__django-13401`: FROM -> ghcr.io/epoch-research/swe-bench.eval.arm64.django__django-13401@sha256:26307abc1ba36b062ecfd8ba0357e3bbfcfb0e1264b9f7ef776bd10c75650608; agent timeout 3000 -> 1200
- `swebench-verified/django__django-13925`: FROM -> ghcr.io/epoch-research/swe-bench.eval.arm64.django__django-13925@sha256:8d223353a1542e377f4bf5695c42fcd2a2fe7bb7e78c8c88eab191bc297a9598; agent timeout 3000 -> 1200
- `swebench-verified/django__django-14376`: FROM -> ghcr.io/epoch-research/swe-bench.eval.arm64.django__django-14376@sha256:a4d53c909207df34e06b1a8a5916a49bd25fe1605c7d32393517f12e90f5e6a7; agent timeout 3000 -> 1200
- `swebench-verified/django__django-14404`: FROM -> ghcr.io/epoch-research/swe-bench.eval.arm64.django__django-14404@sha256:a710bbf5156359b8ce72f505362ffbc03b7d89bc82b2d1a0acb1987bef6cc8ee; agent timeout 3000 -> 1200
- `swebench-verified/django__django-14534`: FROM -> ghcr.io/epoch-research/swe-bench.eval.arm64.django__django-14534@sha256:0a9abe8bd0663ff2eafbc612421baaa0d02d9d6ece0f895d20e1e444b00ef3eb; agent timeout 3000 -> 1200
- `swebench-verified/django__django-14725`: FROM -> ghcr.io/epoch-research/swe-bench.eval.arm64.django__django-14725@sha256:90cb826e1a7072f3b3b5b5d48c979564f8a9fb3622888ce2268350aa3239386d; agent timeout 3000 -> 1200
- `swebench-verified/django__django-16454`: FROM -> ghcr.io/epoch-research/swe-bench.eval.arm64.django__django-16454@sha256:f229e82282009f10dee564650c016e8b05a8033a3a6c16553e6d047b0fdfcb1e; agent timeout 3000 -> 1200
- `swebench-verified/django__django-16950`: FROM -> ghcr.io/epoch-research/swe-bench.eval.arm64.django__django-16950@sha256:dec9c44aa5ef52a811531732a62001ea28fe794f09bfd9f81c74e3bd77beb1cf; agent timeout 3000 -> 1200
- `swebench-verified/sympy__sympy-13031`: FROM -> ghcr.io/epoch-research/swe-bench.eval.arm64.sympy__sympy-13031@sha256:62b9003c0297529ee26425638af9ae8c406514d1c409f415cb9d51f71d680edb; agent timeout 3000 -> 1200
- `swebench-verified/sympy__sympy-14976`: FROM -> ghcr.io/epoch-research/swe-bench.eval.arm64.sympy__sympy-14976@sha256:077064ba433b9b9d1eaa0f95b10bf37170d3e065eb6e2be82edaf604b141d62f; agent timeout 3000 -> 1200
- `swebench-verified/sympy__sympy-18211`: FROM -> ghcr.io/epoch-research/swe-bench.eval.arm64.sympy__sympy-18211@sha256:459e5daffe0a9b8c7513f272afc42ce58e8dc87e253e8b363cbcfcc00d92ea75; agent timeout 3000 -> 1200
- `swebench-verified/pytest-dev__pytest-7490`: FROM -> ghcr.io/epoch-research/swe-bench.eval.arm64.pytest-dev__pytest-7490@sha256:f049336c9c8201e8c61280685655078ee5fdd2c8e087c9830816af9e54e92fe9; agent timeout 3000 -> 1200
- `swebench-verified/mwaskom__seaborn-3069`: FROM -> ghcr.io/epoch-research/swe-bench.eval.arm64.mwaskom__seaborn-3069@sha256:d69b41f4a45e52de029b569c7fd7be022b1e9727cb810ca84907908b65c86510; agent timeout 3000 -> 1200
- `terminal-bench-2-1/cancel-async-tasks`: prebuilt docker_image dropped, built from Dockerfile
- `terminal-bench-2-1/extract-elf`: prebuilt docker_image dropped, built from Dockerfile
- `terminal-bench-2-1/openssl-selfsigned-cert`: prebuilt docker_image dropped, built from Dockerfile
- `terminal-bench-2-1/sanitize-git-repo`: prebuilt docker_image dropped, built from Dockerfile
- `terminal-bench-2-1/sqlite-with-gcov`: prebuilt docker_image dropped, built from Dockerfile
- `terminal-bench-2-1/largest-eigenval`: prebuilt docker_image dropped, built from Dockerfile
- `terminal-bench-2-1/sparql-university`: prebuilt docker_image dropped, built from Dockerfile
- `terminal-bench-2-1/financial-document-processor`: prebuilt docker_image dropped, built from Dockerfile
- `openthoughts-tblite/todos-api`: none
- `openthoughts-tblite/api-endpoint-permission-canonicalizer`: none
- `openthoughts-tblite/build-merkle-tree-cli-sha512`: none
- `openthoughts-tblite/fix_async_worker_queue`: none
- `openthoughts-tblite/pandas-etl`: none
- `openthoughts-tblite/python-api-rate-limit`: none
- `openthoughts-tblite/build-system-task-ordering`: none
- `openthoughts-tblite/application-debug`: none
