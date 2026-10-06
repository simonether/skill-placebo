# Pilot summary (2026-09-29 .. 2026-09-30)

Method: METHOD.md v1.0 (720c192) with amendments 1-8. Pilot data are not reused in the main run.
Costs are estimates from tokens at public API list prices; the runs used subscriptions.

## Claude Code (claude-opus-5-5, effort medium, Claude Code 2.1.282)

- Task trials: 159 valid (78 selection + 16 selection of added tasks + 5 third trials + 60 kill test),
  4 infrastructure retries, 22 calibration runs.
- Per task trial: median 0.053 M units ($0.17), mean 0.060 M units ($0.20). All task trials:
  9.6 M units, $31.9.
- Baseline selection: 41 of 47 tasks passed every trial, 3 passed some (application-debug,
  django-13512, sympy-17630), 3 passed none (django-11141, django-11734, video-processing).
  Opus 5.5 at medium effort sits at the ceiling of this pool.
- Selected set for the main run: 3 qualified + 12 ceiling-flagged (`tasks/selected.json`).
- Plan windows (account-wide, from Claude Code's own `rate_limit_event`): 7-day 4% → 13%;
  the benchmark's share at the calibrated ratio (1% ≈ 5.8 M units) is about 1.7 points.

### Kill test (5 tasks x 2 trials per arm)

| Skill | Placebo | Cost ratio R [95% CI] | Pass skill / placebo | Output tokens skill / placebo |
|---|---|---|---|---:|
| caveman | cc-5 | 1.02 [0.83, 1.26] | 100% / 100% | 5,187 / 5,519 |
| ponytail | cc-4 | 0.75 [0.63, 0.88] | 100% / 100% (90% before the verifier rerun) | 3,004 / 4,749 |
| i-have-adhd | cc-3 | 0.72 [0.60, 0.92] | 100% / 100% | 4,602 / 6,620 |

Kill rule (section 11.3): not killed; ponytail and i-have-adhd show non-trivial cost differences.
One kill-test trial (placebo-cc-5 x django-15957) ran without its placebo (directory rebuilt during
the run) and was repeated; see the log of 29.09.
One kill-test trial (placebo-cc-4 x fix_async_worker_queue) had a verifier timeout. Under amendment 9
its verifier was rerun on its reconstructed final state and passed (11 of 11 tests in 16 s; the task
without the agent's changes fails 5 of 11), so it counts as passed and its episode is flagged as
infrastructure. R is unchanged.

## Codex (gpt-6-sol, effort medium, Codex CLI 0.157.0, ChatGPT Plus)

- Task trials: 97 valid (47 selection + 50 kill test), 4 infrastructure retries, 23 calibration runs.
- Per task trial: median 0.075 M units ($0.15), mean 0.106 M units ($0.21). All task trials:
  10.3 M units, $20.5.
- Baseline selection (1 trial per task): 32 of 47 passed, 15 failed. No ceiling on Codex.
- Plan: weekly 12% → 37% (+25 points, the stop threshold, reached with the last kill-test trial);
  the 5-hour window reached the 40% pause threshold, five 60-minute pauses.

### Kill test (5 tasks x 2 trials per arm)

| Skill | Placebo | Cost ratio R [95% CI] | Pass skill / placebo | Output tokens skill / placebo |
|---|---|---|---|---:|
| ponytail | cx-4 | 1.09 [0.90, 1.23] | 90% / 100% | 4,438 / 4,756 |
| agent-skills | cx-5 | 1.24 [1.10, 1.42] | 100% / 80% | 5,634 / 4,917 |
| compound-engineering | cx-4 | 1.42 [1.23, 1.64] | 100% / 100% | 5,650 / 4,756 |

Kill rule: not killed; agent-skills and compound-engineering cost more than their placebo.

## Design of the main run by the pre-registered thresholds (section 11.3, amendments 2-3)

- Claude Code: 9.6 M units / $31.9 for 159 task trials ≈ 9.1 M units / $30 per 150 → at most
  17 M units and $45 → **Full design** (9 skills, 15 tasks as selected, N = 5; 15 arms x 75 = 1,125
  trials; ≈ 68 M units ≈ 12 points of the week at the calibrated ratio).
- Codex: +25 points of the Plus weekly limit for 97 task trials + 23 calibration runs ≈ 31 points
  per 150 runs → above 6% → Minimal; even Minimal (8 arms x 45 = 360) needs ≈ 76 points, and
  the next Codex week allows 25 → about 100 trials, fewer than 10 tasks. By section 11.3 Codex is
  dropped from the main run unless the owner changes the plan.

Other observations: the scripted approval turn fired in 1 task trial per harness; Codex read a
skill's SKILL.md in 30 task trials; Claude Code skills in the kill test act through hooks, not the
Skill tool.
