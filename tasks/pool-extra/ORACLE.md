# Oracle check of the staged harder candidates (2026-09-29)

Harbor 0.23.0 `oracle` agent, 2 attempts, local Docker on macOS arm64. Rule (METHOD.md section 6):
a task that does not pass both attempts cannot enter the pool.

| Source | Task | Attempts | Eligible |
|---|---|---|---|
| swebench-verified | django__django-11141 | 1.0 1.0 | yes |
| swebench-verified | django__django-11734 | 1.0 1.0 | yes |
| swebench-verified | django__django-13512 | 1.0 1.0 | yes |
| swebench-verified | django__django-14140 | 1.0 1.0 | yes |
| swebench-verified | django__django-16256 | 1.0 1.0 | yes |
| swebench-verified | sphinx-doc__sphinx-10435 | 1.0 1.0 | yes |
| swebench-verified | sympy__sympy-17630 | 1.0 1.0 | yes |
| terminal-bench-2-1 | make-doom-for-mips | 0.0, AgentTimeoutError | **no** (reference solution does not finish in the 900 s agent timeout on arm64) |
| terminal-bench-2-1 | video-processing | 1.0 1.0 | yes |

8 of 9 staged candidates are eligible.
