# skill-placebo: pre-registered method

Version 1.0 draft, 2026-09-28. This file is committed to git before any benchmark run. The commit
history is the timestamp of the pre-registration. After the first run the method changes only
through the [Amendments](#16-amendments) section: date, reason, which runs are affected, written
before those runs.

<!-- DRAFT: sections marked TBD are filled from docs/research/ before the pre-registration commit. -->

## 1. Question

Popular agent skills and plugins for coding agents promise better work, fewer tokens, or both.
Most of these promises were never tested against a control that accounts for the simplest
alternative explanation: *any* extra instruction of the same length changes what the agent does and
what it costs.

For each of the most-starred general-purpose coding skills (nine qualify, section 3) we ask:

1. **Does the skill beat a placebo?** A placebo is a neutral instruction of the same length,
   installed the same way, that adds no new direction.
2. **What does the skill do to cost?** Mean USD per task at list prices, and per solved task.

Secondary questions: skill vs no skill; placebo vs no skill (the size of the placebo effect itself);
the author's README claim vs the measured number, where the README makes a numeric claim.

## 2. Prior art

This project is a replication and extension, not a first. What was already measured:

| Work | Date | What it did | Result |
|---|---|---|---|
| JetBrains AI blog: [caveman](https://blog.jetbrains.com/ai/2026/07/speak-to-ai-agents-like-cavemen-tosave-tokens/) | 2026-07 | Harbor 0.17, Claude Code, Sonnet 5 low effort, 86 SkillsBench tasks, skill forced on | output tokens -8.5% (claimed 65%), cost about -10%, quality sign test p = 0.82 |
| JetBrains: [ponytail](https://blog.jetbrains.com/ai/2026/07/ponytail-skill-claude-tested/) | 2026-07 | Harbor 0.18, Sonnet 5 medium, 80 paired tasks, 251 trials; ruleset forced (installed normally it self-activated 0 of 10 times) | cost -10.3% (p = 0.004), code -15.4% (p = 0.088), quality no difference; no placebo arm |
| JetBrains: [rtk](https://blog.jetbrains.com/ai/2026/07/rtk-claude-code-token-savings/) | 2026-07 | same setup, 425 trials (a CLI proxy, out of scope here) | cost +7.6% at low effort (p = 0.004) against claimed -60..-90% |
| [Scott Logic on ponytail](https://blog.scottlogic.com/2026/06/16/ponytail-yagni-and-the-problem-with-prompt-benchmarks.html) | 2026-06 | promptfoo, single-shot, Claude Haiku | a seven-word "Follow YAGNI principles, and one-liner solutions" prompt beat the skill on its own benchmark |
| [maxtaylor.me: caveman vs "Be brief."](https://www.maxtaylor.me/articles/i-benchmarked-caveman-against-two-words) | 2026-04 | 24 chat prompts, Opus 4.7, 5 arms (HN 47954745) | "Be brief." matched caveman on tokens and quality |
| [MindStudio on superpowers](https://www.mindstudio.ai/blog/5-claude-code-skills-cut-token-costs-70-percent-benchmarked) | 2026 | 6 sessions with vs 6 without | -9% cost, -14% tokens, no CI |
| [SWE-Skills-Bench](https://arxiv.org/abs/2603.15401) | 2026-03 | 49 public SWE skills, paired with/without | 39 of 49 with zero pass-rate gain, mean +1.2% |
| [SkillsBench](https://arxiv.org/abs/2602.12670) | 2026-02 | curated task-specific skills, 87 tasks | curated skills help; general workflow skills not studied |
| [ACES / NVIDIA SkillEvaluator](https://arxiv.org/abs/2608.20614) | 2026-08 | paired with/without on Harbor, 145 enterprise skills | mean "Skill Lift" 0.21 |
| Tessl registry | 2026 | auto-generated scenario evals | karpathy-guidelines "1.14x"; superpowers: only brainstorming has evals |
| sjh9714/skill-receipts, currenjin/skillbench | 2026-07 | the same idea (placebo arm; weekly with baseline) | no published results found |
| `claude plugin eval` (Claude Code 2.1.269) | 2026-09-11 | first-party with/without ablation for one plugin | a tool; no placebo arm, no public comparison |

The closest thing to a placebo result so far is two active controls ("Be brief.", the YAGNI prompt)
on single-shot prompts. Numbers above are as each source reports them.

What this project adds: nine skills in one design; a length-matched placebo arm; two harnesses
(Claude Code and Codex CLI); the method fixed before data; README claims next to measured numbers;
every trajectory published.

## 3. Skills under test

Source: `docs/research/2026-09-28-skills-census.md` (stars, components, install docs, claims, with
file:line at the pinned commit). Pins: `skills.lock.json`.

**Selection rule.** The most-starred skills or plugins for coding agents on 2026-09-28 that plausibly
change behaviour on *any* coding task (workflow discipline, planning, testing, brevity, engineering
guidelines). Excluded: domain skills (design, docs, SEO), memory systems, orchestrators, CLI proxies,
collections of unrelated skills. Nine pass; no tenth fits the rule, so the study runs nine.

**Pinned version:** the default-branch commit on 2026-09-28, which is what a marketplace install
gets that day.

| # | Skill | Stars (28.09) | Commit | Type in Claude Code | Always-on chars (CC) | Numeric README claim | Prior independent measurement |
|---|---|---:|---|---|---:|---|---|
| 1 | addyosmani/agent-skills | 99,510 | 2686b62 | triggered pack: 25 skills, 9 commands, 4 agents | 10,973 | none | none found |
| 2 | mattpocock/skills | 270,709 | c55ee46 | triggered pack: 25 skills | 4,106 | none | none found |
| 3 | ayghri/i-have-adhd | 51,606 | 839872f | documented always-on mode: SessionStart hook | 7,291 | none | none found |
| 4 | OthmanAdi/planning-with-files | 27,154 | 51c1caa | triggered; hooks once a plan file exists | 2,646 | 96.7% (29/30), 13.3 → 5.0 turns (`README.md:33-34,75`) | none found |
| 5 | EveryInc/compound-engineering-plugin | 25,299 | e80c5c4 | triggered pack: 36 skills | 7,943 | none | none found |
| 6 | multica-ai/andrej-karpathy-skills | 215,547 | 2c60614 | always-on CLAUDE.md (the author's "single CLAUDE.md file") | 2,345 | none | Tessl scenario eval only |
| 7 | obra/superpowers | 292,189 | 8ca22db | 15 skills + SessionStart hook | 6,020 | none | MindStudio, 6 vs 6 sessions |
| 8 | DietrichGebert/ponytail | 146,942 | e3ba2aa | 6 skills + SessionStart ruleset hook | 7,874 | ~54% less code, ~20% cheaper, ~27% faster (`README.md:33`) | JetBrains 2026-07: cost -10.3% (p=0.004), no placebo |
| 9 | JuliusBrussee/caveman | 108,076 | 2fd153c | 20 skills + 3 agents + SessionStart and per-prompt hooks | 10,043 (+245 per prompt) | "cuts 65% of tokens" (repo description) | JetBrains 2026-07: -8.5% output tokens; maxtaylor.me: "Be brief." matched it |

Always-on characters are measured, not estimated: `scripts/measure_always_on.py` takes exactly the
components Claude Code lists for the plugin (`claude plugin details`) and runs the plugin's
SessionStart hooks for real (`placebo/always_on.json`).

The table order is the **priority order**: skills nobody has measured independently come first
(task brief). The reduced designs (section 11.3) take the first 8 or 6.

**Excluded, with reasons:** affaan-m/ECC (268k stars; 292 skills plus memory and a harness layer),
Leonxlnx/taste-skill (91k; frontend design), open-gsd/gsd-core, formerly get-shit-done (64k archived +
10k; a phase orchestrator driven by user commands). Full list in the census.

**Codex:** TBD, hub decision pending: skills whose author documents a Codex install that works
without a per-session manual command.

**superpowers:** TBD, hub decision pending: its brainstorming skill stops for the user's approval and
the author documents no unattended mode.

## 4. Arms

Every task is run in every arm on every harness with the same model, effort, container image,
tools, permissions, timeout and prompt. Only the installed instruction differs.

| Arm | What is installed |
|---|---|
| **Baseline** | Nothing. Harness defaults. |
| **Placebo** | A neutral instruction of the same length as the skill, installed through the same mechanism. |
| **Skill** | The skill or plugin, installed exactly as its author documents, at the pinned commit. |

### 4.1 Placebo construction

**Buckets.** Skills whose always-on text lies within +-10% of a common length share one placebo.
Claude Code (`placebo/buckets.json`):

| Placebo | Members (always-on chars) | Placebo chars | Largest deviation |
|---|---|---:|---:|
| cc-a | karpathy (2,345), planning-with-files (2,646) | 2,495 | +6.4% |
| cc-b | mattpocock (4,106) | 4,106 | 0% |
| cc-c | superpowers (6,020) | 6,020 | 0% |
| cc-d | i-have-adhd (7,291), ponytail (7,874), compound-engineering (7,943) | 7,703 | +5.7% |
| cc-e | caveman (10,043), agent-skills (10,973) | 10,508 | +4.6% |

**Form.** Each placebo is a plugin in the same format as the real ones (`arms/placebo/<bucket>/`,
`src/skill_placebo/placebo.py`): k neutral skills whose names and descriptions add up to the
members' mean listing length (k = the members' mean number of listed components); a SessionStart
hook that injects neutral text of the members' mean hook-plus-memory length; skill bodies of the
members' mean body length. The split between listing and injected text is the bucket mean, so in
mixed buckets the mechanism is matched approximately and the length exactly.

**Token check before any task.** Characters are not tokens. The pilot starts with one trivial prompt
per arm; the input tokens of the first request minus baseline give each arm's always-on tokens. If a
placebo differs from any member of its bucket by more than 10% in tokens, the placebo is rescaled and
checked again before any task trial (recorded as an amendment).

Also fixed:

- The placebo text restates guidance the harness already gives by default (read the task, use the
  available tools, check the work) in neutral wording. It adds length and the presence of an
  instruction, but no new direction on process, verbosity, testing, planning or tool choice.
- It contains no words from the tested skills' names or trigger phrases.
- Length is matched in characters of the text that reaches the model at session start, and token
  counts are reported next to it.
- The placebo corpus is committed in `placebo/` before the first run and never edited afterwards
  except through an amendment.

## 5. Harnesses and models

Research behind these choices: `docs/research/2026-09-25-harness-infra.md`.

| | Claude Code | Codex CLI |
|---|---|---|
| Version | 2.1.282 | 0.157.0 |
| Model | `claude-opus-5-5` | `gpt-6-sol` |
| Reasoning effort | Claude Code's default for this model: medium (code.claude.com/docs/en/model-config: "Opus 5.5 defaults to `medium`"), passed explicitly | Codex's default for this model: medium, passed explicitly |
| Permissions | `bypassPermissions` (Harbor default) | `--dangerously-bypass-approvals-and-sandbox` (Harbor default) |
| Built-in web tools | disabled: `WebSearch`, `WebFetch` | disabled: `web_search = "disabled"` |
| Login | owner's Claude Max subscription via a dedicated long-lived token (`claude setup-token`) | owner's ChatGPT subscription via a separate Codex login (`codex login --device-auth` in its own `CODEX_HOME`) |

- Runner: Harbor 0.23.0 (`harbor-framework/harbor`), local Docker Desktop, native `linux/arm64`
  images, concurrency at most 2. One Harbor job per trial so that the order and the stop rules are
  controlled by `src/skill_placebo/runner.py`. Harbor is started with a clean environment: only the
  one harness's login, telemetry off.
- Agent timeout: the task's own, capped at 1,200 s. No turn limit, so that multi-step workflows are
  not cut short by the harness. A timeout is a failed trial.
- Opus 5.5 is the newest Claude model and what subscribers run in Claude Code; effort is the
  harness default, so the setup matches everyday use (owner's choice, 2026-09-28). `gpt-6-sol` is the
  model Codex documents for "complex coding and agentic workflows"
  (`learn.chatgpt.com/docs/models`, 2026-09-25), at Codex's default effort for it. The effort
  value is passed explicitly, equal to the default, so that a change of defaults in a later
  harness release cannot change the setup; it is recorded in every trial.
- Web tools are off in every arm because the fixes for public benchmark tasks are on GitHub. The
  shell still has network access (the agent needs it to reach the model). Trials that fetch the
  upstream repository of a SWE-bench task are flagged in the data.
- Permissions: the documented non-interactive mode in every arm. Interactive plugins run only in a
  mode their authors document for unattended use; the table marks them.
- **Versions are frozen for a run.** Harness versions, model IDs, Harbor version, skill commits and
  image digests are pinned before the pilot and recorded in every trial's result. If a harness or
  skill releases an update during a run, the run finishes on the pinned version; the update is at
  most a later rerun.
- One container image per task, identical across arms. Every plugin directory is mounted read-only
  in every arm; only an environment variable decides whether a plugin loads, so the file systems
  of the arms do not differ.
- **Subscriptions, not API keys.** The owner chose to run on existing subscriptions. Nothing is
  billed per token, so every cost in this study is an **estimate from tokens**: recorded input,
  cache write, cache read and output tokens times the public API list price on 2026-09-25
  (`src/skill_placebo/collect.py`). The tables label it that way.

## 6. Tasks

Research: `docs/research/2026-09-25-task-pool.md`. SkillsBench is not used: about half of its
tasks need domain knowledge that a general workflow skill cannot supply, and several of its images
ship skills that would leak into the control arms.

- **Candidate pool: 30 tasks** with deterministic test-based verifiers, no LLM judges, vendored at
  pinned upstream commits in `tasks/pool/` (`manifest.json`, `PATCHES.md`):
  - 14 SWE-bench Verified (real bug fixes and small features in django, sympy, pytest, seaborn),
    picked where 2-4 of 6 frontier-model runs pass. Images: Epoch's arm64 builds, pinned by digest.
  - 8 Terminal-Bench 2.1 (scripting, parsing, build, performance, data processing), built from
    their own Dockerfiles.
  - 8 OpenThoughts-TBLite (bug fixes and features in small Python services and CLIs).
- Patches are identical for every arm: base image for arm64, agent timeout cap. Nothing in any
  instruction, test or solution is changed.
- **Oracle check:** every pool task passes with its reference solution 2 of 2 times on the runner
  (`tasks/pool/ORACLE.md`, 2026-09-25).
- **Selection** (Claude Code baseline arm, in the pilot):
  1. Every pool task runs 2 times. Tasks with 1 of 2 passes qualify.
  2. If fewer than 20 qualify, tasks at 0/2 or 2/2 get a third trial, in the seeded order, while the
     pilot cap allows; 1/3 and 2/3 qualify.
  3. If more than 20 qualify, 20 are drawn with seed 20260928, keeping the source mix as close to
     the pool's as possible (14:8:8).
  4. If fewer than 15 qualify, the set is filled to 15 with tasks that passed every pilot trial, in
     the seeded order. They carry no pass-rate information but still measure cost; they are flagged.
- The candidate list, seed and pilot results are committed before the main run.
- **Pilot runs are not reused as main-run data.** Selecting tasks on baseline results and then
  reusing those results would bias the baseline (regression to the mean). The main run repeats the
  baseline from scratch.
- The same 20 tasks are used on both harnesses. The Codex baseline pass rate is reported as
  observed, even if it falls outside 30-70%.
- Tasks are public and may be in model training data. Contamination affects all arms equally, so
  within-harness comparisons stay valid; absolute pass rates are not claimed to generalise.

## 7. Procedure

- N = 5 trials per task per arm per harness in the full design (section 11.3 for the reduced ones).
- Order: trials are interleaved in randomized blocks (one block = every arm on every task once), so
  that drift in model serving over the run window affects all arms equally. The seed is committed.
- Infrastructure failures (container did not start, API 5xx or rate limit before the agent's first
  action, verifier crashed) are retried up to 2 times and logged. Agent failures (timeout, turn
  limit, gave up, broke the environment) are not retried: they count as failed trials and their cost
  counts.
- Every trial is kept, including failed and aborted ones, with the reason.

## 8. Outcomes

Primary, per trial:

1. **Cost** in USD, computed from recorded token usage (input, cache write, cache read, output) at
   the provider's list prices on the run date. The price table is committed with the results.
2. **Pass**: verifier reward = 1.

Secondary: tokens by type; turns; tool calls; wall time; USD per solved task (total cost / trials
passed); size of the final diff.

## 9. Analysis

All comparisons are within one harness and paired by task.

- **Cost ratio** R = mean cost (skill) / mean cost (placebo). **Pass difference** D = pass rate
  (skill) - pass rate (placebo), in percentage points.
- 95% confidence intervals by cluster bootstrap over tasks: resample tasks with replacement (the
  same tasks for both arms), keep all trials of each resampled task, 10,000 resamples, seed
  20260925. Two-sided p-values from the same bootstrap distribution. Implementation:
  `src/skill_placebo/analysis.py`, committed before any data.
- Multiple comparisons: Holm correction across the 10 skills, separately per harness and per
  outcome. Tables show unadjusted 95% CIs; verdicts use Holm-adjusted p < 0.05.
- The same statistics are reported for skill vs baseline and placebo vs baseline.

### 9.1 Verdict per skill and harness

An outcome **improves** when the adjusted p < 0.05 in the good direction (R < 1, D > 0) and
**worsens** when adjusted p < 0.05 in the bad direction.

| Verdict | Rule |
|---|---|
| **Beats placebo** | at least one outcome improves, none worsens |
| **Trade-off** | one outcome improves, the other worsens |
| **Worse than placebo** | at least one outcome worsens, none improves |
| **No better than placebo** | nothing improves or worsens |

When "beats placebo" rests on cost alone, the table also shows how much worse the pass rate could
be (the lower CI bound of D).

### 9.2 What goes in the headline

- The cost change vs placebo (R with its CI) and the verdict.
- Not the pass-rate difference: with 20 tasks x 5 trials the CI on D is about +-14 pp, too wide for
  a headline. D is in the table with its CI.
- Every number is shown with its CI and the control arm next to it. "Ceiling" means the CI bound:
  the largest effect the data allow.

## 10. README claims vs measured

For skills whose README makes a numeric claim, the table shows the claim (quote, file, line, commit)
next to the measured quantity closest to it (for example, total tokens for a token-savings claim)
vs baseline and vs placebo, with CIs. Skills without numeric claims get no "claimed" column entry;
they get the verdict only.

## 11. Pilot and kill test

The pilot is capped at 150 trials per harness and runs with concurrency 2.

### 11.1 Claude Code (at most 150 runs)

- Token check (section 4.1): one trivial prompt per arm, 15 runs.
- Task selection (section 6): 40 pool tasks x 2 baseline trials = 80, plus at most 5 third trials.
- Kill test: caveman, ponytail and i-have-adhd with their placebos cc-e and cc-d (5 arms), on 5
  tasks drawn from the pool with seed 20260928 before the pilot (3 SWE-bench, 1 TB2.1, 1 TBLite),
  2 trials each = 50. These three are chosen because they put the most always-on text into the
  context without any interactive gate, so they are the likeliest to move cost if anything does.

### 11.2 Codex (at most 100 runs)

- Token check for the Codex arms.
- 40 pool tasks x 1 baseline trial: checks that every task runs under Codex and gives a first base
  rate.
- Kill test on Codex with the Codex-eligible skills among the three above plus the next ones in
  priority order, up to 5 arms x 5 tasks x 2 = 50.

### 11.3 Kill rule and the size of the main run

- **Kill rule.** If no skill on either harness shows a non-trivial cost difference vs its placebo,
  the project stops at a write-up without a repo release. Non-trivial means a point estimate of R
  outside 0.90-1.10 **and** a 95% CI that excludes 1. With 6 tasks the CI is wide; the gate only
  asks whether anything moves at all.
- **Size of the main run** is chosen after the pilot, from resource numbers only (share of the
  weekly subscription limit per trial, wall time per trial), never from effect estimates:

  | Design | Skills | Tasks | N | Arms per harness |
  |---|---|---|---|---|
  | Full | 10 | 20 | 5 | baseline + placebos + 10 |
  | Reduced | first 8 in priority order | first 15 of the selected set, seeded order | 3 | baseline + placebos + 8 |
  | Minimal | first 6 | 15 | 3 | baseline + placebos + 6 |

  **Thresholds**, applied per harness to pilot measurements only:
  - `u` = share of the plan's weekly limit used per trial (pilot total / pilot trials);
  - `t` = mean wall time per trial at concurrency 2;
  - `H` = hours from the start of the main run to 2026-10-09 12:00 MSK, minus 12 hours of reserve;
  - `L` = 25% of the weekly limit per weekly period, times the number of weekly periods the main
    run overlaps (1 unless the plan's reset falls inside the window), unless the owner sets a
    different ceiling before the main run.

  The main run uses the **largest** design D with `trials(D) x u <= L` **and**
  `trials(D) x t / 2 <= H`, where trials(D) counts every arm including baseline and placebos. If not
  even the minimal design fits on a harness, that harness runs the minimal design on as many of the
  15 tasks as fit, in the seeded order, and the gap is reported; if that leaves fewer than 10 tasks
  the harness is dropped from the main run and the owner is asked. The choice and the numbers
  behind it are recorded as an amendment before the main run.
- Pilot trials are not reused in the main analysis. The pilot's own numbers are published
  separately.

## 12. Budget and stop rules

Runs use the owner's subscriptions, whose weekly limits are shared with his other work. The
runner stops the batch and the result is reported to the owner when:

- the benchmark has used more than 25% of the weekly limit of either plan since the batch started
  (Codex: the weekly `used_percent` in session logs; Claude: the plan's usage page, read before and
  after each batch);
- any trial shows a limit warning, a rate-limit error or an authentication failure (structured
  harness events only, so a task that itself deals with HTTP 401/429 cannot trigger it);
- Docker Hub throttles image pulls.

Usage before and after every batch is recorded in `docs/budget.md` together with the token-based
cost estimate.

## 13. Limitations

- **Contamination.** SWE-bench Verified (public since 2024) and Terminal-Bench 2 (public since
  2025) are probably in the training data of both models, and solutions to them are published. This
  inflates absolute pass rates on these tasks. It affects all arms equally, so the comparisons
  skill vs placebo vs baseline stay fair, but the absolute pass rates here say little about new,
  unseen work. A fresh-task rerun (for example a recent SWE-rebench slice) is the planned check.
- **Two models, default effort.** Results are for Opus 5.5 and gpt-6-sol at their harness default
  effort in headless mode. Other models, effort levels or interactive use can behave differently.
- **No direct comparison with JetBrains.** The JetBrains series used Sonnet 5 on SkillsBench; this
  study uses Opus 5.5 on a different task set. Where both measured the same skill, the numbers are
  shown side by side as context, not as a replication.
- **Short tasks.** Tasks take minutes, not days. Skills that pay off over long sessions (memory,
  multi-day planning) are not measured by this design.
- **Headless.** Interactive skills run in their documented unattended mode, which is not how every
  user runs them.
- **Power.** With 20 tasks x 5 trials the 95% CI on a pass-rate difference is about +-14 pp; smaller
  effects on quality are not detectable. Cost differences are measured more precisely.
- **Cost is estimated from tokens.** Runs used subscriptions; cost is tokens x public list prices,
  not an invoice.

## 14. Fairness to skill authors

- Each skill is installed the way its author documents, at a pinned commit, including hooks,
  agents and commands when the author ships them.
- Results go to the authors of the tested skills 48 hours before publication. Replies are linked
  from the results page. Installation errors found by authors are fixed and the affected skill's
  arms are rerun in full before publication (an amendment records it).
- Neutral wording. The results say what was measured, on which tasks and models, and nothing about
  intent.

## 15. Reproduction and data release

- One command reproduces a skill's row: `uvx skill-placebo run <owner/repo>` (TBD exact flags).
- Raw trajectories, verifier outputs, token usage and the analysis notebook are published.
- Before release every artifact passes `scripts/scrub.py --check`: no API keys, no local paths,
  no personal e-mail.

## 16. Amendments

None yet.
