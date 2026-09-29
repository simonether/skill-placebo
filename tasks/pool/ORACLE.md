# Oracle check of the task pool

Harbor 0.23.0 `oracle` agent (reference solutions, no model calls), 2 attempts per task, local
Docker Desktop on macOS arm64 (native linux/arm64 images). SWE-bench tasks checked 2026-09-28 after
the grader-dependency patch; Terminal-Bench 2.1 (original 8) and TBLite checked 2026-09-25, the 4
added Terminal-Bench 2.1 tasks 2026-09-28. Scripts: `scripts/oracle_check.sh`, `scripts/oracle_tasks.sh`.

Rule (METHOD.md section 6): a task that does not pass both attempts leaves the pool.

| Source | Task | Attempts | In pool |
|---|---|---|---|
| swebench-verified | django__django-10973 | 1.0 1.0 | yes |
| swebench-verified | django__django-13401 | 1.0 1.0 | yes |
| swebench-verified | django__django-13925 | 1.0 1.0 | yes |
| swebench-verified | django__django-14376 | 1.0 1.0 | yes |
| swebench-verified | django__django-14404 | 1.0 1.0 | yes |
| swebench-verified | django__django-14534 | 1.0 1.0 | yes |
| swebench-verified | django__django-14725 | 1.0 1.0 | yes |
| swebench-verified | django__django-16454 | 1.0 1.0 | yes |
| swebench-verified | django__django-16950 | 1.0 1.0 | yes |
| swebench-verified | sympy__sympy-13031 | 1.0 1.0 | yes |
| swebench-verified | sympy__sympy-14976 | 1.0 1.0 | yes |
| swebench-verified | sympy__sympy-18211 | 1.0 1.0 | yes |
| swebench-verified | pytest-dev__pytest-7490 | 1.0 1.0 | yes |
| swebench-verified | mwaskom__seaborn-3069 | 1.0 1.0 | yes |
| swebench-verified | django__django-11265 | 1.0 1.0 | yes |
| swebench-verified | django__django-15957 | 1.0 1.0 | yes |
| swebench-verified | django__django-11885 | 1.0 1.0 | yes |
| swebench-verified | django__django-15563 | 1.0 1.0 | yes |
| swebench-verified | django__django-15973 | 1.0 1.0 | yes |
| swebench-verified | pylint-dev__pylint-7080 | 1.0 1.0 | yes |
| terminal-bench-2-1 | cancel-async-tasks | 1.0 1.0 | yes |
| terminal-bench-2-1 | extract-elf | 1.0 1.0 | yes |
| terminal-bench-2-1 | openssl-selfsigned-cert | 1.0 1.0 | yes |
| terminal-bench-2-1 | sanitize-git-repo | 1.0 1.0 | yes |
| terminal-bench-2-1 | sqlite-with-gcov | 1.0 1.0 | yes |
| terminal-bench-2-1 | largest-eigenval | 1.0 1.0 | yes |
| terminal-bench-2-1 | sparql-university | 1.0 1.0 | yes |
| terminal-bench-2-1 | financial-document-processor | 1.0 1.0 | yes |
| terminal-bench-2-1 | query-optimize | 1.0 1.0 | yes |
| terminal-bench-2-1 | write-compressor | 1.0 1.0 | yes |
| terminal-bench-2-1 | headless-terminal | 1.0 1.0 | yes |
| terminal-bench-2-1 | adaptive-rejection-sampler | VerifierTimeoutError 1.0 | **no** |
| openthoughts-tblite | todos-api | 1.0 1.0 | yes |
| openthoughts-tblite | api-endpoint-permission-canonicalizer | 1.0 1.0 | yes |
| openthoughts-tblite | build-merkle-tree-cli-sha512 | 1.0 1.0 | yes |
| openthoughts-tblite | fix_async_worker_queue | 1.0 1.0 | yes |
| openthoughts-tblite | pandas-etl | 1.0 1.0 | yes |
| openthoughts-tblite | python-api-rate-limit | 1.0 1.0 | yes |
| openthoughts-tblite | build-system-task-ordering | 1.0 1.0 | yes |
| openthoughts-tblite | application-debug | 1.0 1.0 | yes |

39/40 tasks pass both attempts and stay in the pool.

Added 2026-09-29 (amendment 6), oracle 2026-09-29 (`tasks/pool-extra/ORACLE.md`): swebench-verified/django__django-13512, swebench-verified/django__django-14140, swebench-verified/django__django-11141, swebench-verified/sphinx-doc__sphinx-10435, swebench-verified/django__django-16256, swebench-verified/sympy__sympy-17630, swebench-verified/django__django-11734, terminal-bench-2-1/video-processing - all 2/2.
