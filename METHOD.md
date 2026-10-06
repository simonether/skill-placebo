# skill-placebo: pre-registered method

Version 1.0, 2026-09-28. This file is committed to git before any benchmark run. The commit
history is the timestamp of the pre-registration. After the first run the method changes only
through the [Amendments](#16-amendments) section: date, reason, which runs are affected, written
before those runs.

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
gets that day. Every install is made from a local checkout of that commit, never from a marketplace
that would fetch a newer HEAD.

The table order is the **priority order**: by stars (maintainers' decision, 2026-09-28). The reduced
designs in section 11.3 drop skills from the bottom of the table.

| # | Skill | Stars (28.09) | Commit | Type in Claude Code | Always-on chars (CC) | On Codex | Numeric README claim | Prior independent measurement |
|---|---|---:|---|---|---:|---|---|---|
| 1 | obra/superpowers | 292,189 | 8ca22db | 15 skills + SessionStart hook; interactive (see 5.1) | 6,020 | plugin, no hook (2,615) | none | MindStudio, 6 vs 6 sessions |
| 2 | mattpocock/skills | 270,709 | c55ee46 | triggered pack: 25 skills | 4,106 | skills via `npx skills` path (4,106) | none | none found |
| 3 | multica-ai/andrej-karpathy-skills | 215,547 | 2c60614 | always-on CLAUDE.md (the author's "single CLAUDE.md file") | 2,345 | not run: no Codex install documented | none | Tessl scenario eval only |
| 4 | DietrichGebert/ponytail | 146,942 | e3ba2aa | 6 skills + SessionStart ruleset hook | 7,874 | plugin + hooks (8,347) | ~54% less code, ~20% cheaper, ~27% faster (`README.md:33`) | JetBrains 2026-07: cost -10.3% (p=0.004), no placebo |
| 5 | JuliusBrussee/caveman | 108,076 | 2fd153c | 20 skills + 3 agents + SessionStart and per-prompt hooks | 10,043 (+245 per prompt) | not run: needs a manual /caveman every session | "cuts 65% of tokens" (repo description) | JetBrains 2026-07: -8.5% output tokens; maxtaylor.me: "Be brief." matched it |
| 6 | addyosmani/agent-skills | 99,510 | 2686b62 | triggered pack: 25 skills, 9 commands, 4 agents | 10,973 | plugin (9,266) | none | none found |
| 7 | ayghri/i-have-adhd | 51,606 | 839872f | documented always-on mode: SessionStart hook | 7,291 | not run: needs an explicit $i-have-adhd every session | none | none found |
| 8 | OthmanAdi/planning-with-files | 27,154 | 51c1caa | triggered; hooks once a plan file exists | 2,646 | plugin + hooks (625) | 96.7% (29/30), 13.3 → 5.0 turns (`README.md:33-34,75`) | none found |
| 9 | EveryInc/compound-engineering-plugin | 25,299 | e80c5c4 | triggered pack: 36 skills | 7,943 | plugin (7,943) | none | none found |

Always-on characters are measured, not estimated. Claude Code: `scripts/measure_always_on.py` takes
exactly the components Claude Code lists for the plugin (`claude plugin details`) and runs the
plugin's SessionStart hooks for real (`placebo/always_on.json`). Codex: every SKILL.md the Codex
manifest exposes (Codex does not support `disable-model-invocation`) plus the Codex hooks' output
(`placebo/always_on_codex.json`).

**Codex runs six skills**: those whose author documents a Codex install that works without a manual
command in every session. The other three are marked "not run on Codex" with the reason above.

**Excluded, with reasons:** affaan-m/ECC (268k stars; 292 skills plus memory and a harness layer),
Leonxlnx/taste-skill (91k; frontend design), open-gsd/gsd-core, formerly get-shit-done (64k archived +
10k; a phase orchestrator driven by user commands). Full list in the census.

## 4. Arms

Every task is run in every arm on every harness with the same model, effort, container image,
tools, permissions, timeout, prompt and approval rule (5.1). Only the installed instruction differs.

| Arm | What is installed |
|---|---|
| **Baseline** | Nothing. Harness defaults. |
| **Placebo** | A neutral instruction of the same length as the skill, installed through the same mechanism. |
| **Skill** | The skill or plugin, installed exactly as its author documents, at the pinned commit. |

### 4.1 Placebo construction

**Bucketing rule** (`src/skill_placebo/placebo.py: assign_buckets`, with tests). Sort the skills of
one harness by always-on length; add each skill to the current bucket if the bucket's new mean
length, which is the placebo's length, stays within +-10% of every member; otherwise start a new
bucket. One placebo per bucket. The rule, not a hand choice, forms the buckets.

**Buckets from measured characters** (`placebo/buckets.json`):

| Placebo | Harness | Members (always-on chars) | Placebo chars | Largest deviation |
|---|---|---|---:|---:|
| cc-1 | Claude Code | karpathy (2,345), planning-with-files (2,646) | 2,495 | +6.4% |
| cc-2 | Claude Code | mattpocock (4,106) | 4,106 | 0% |
| cc-3 | Claude Code | superpowers (6,020) | 6,020 | 0% |
| cc-4 | Claude Code | i-have-adhd (7,291), ponytail (7,874), compound-engineering (7,943) | 7,703 | +5.7% |
| cc-5 | Claude Code | caveman (10,043), agent-skills (10,973) | 10,508 | +4.6% |
| cx-1 | Codex | planning-with-files (625) | 625 | 0% |
| cx-2 | Codex | superpowers (2,615) | 2,615 | 0% |
| cx-3 | Codex | mattpocock (4,106) | 4,106 | 0% |
| cx-4 | Codex | compound-engineering (7,943), ponytail (8,347), agent-skills (9,266) | 8,518 | +7.2% |

**Form.** Each placebo is a plugin in the same format as the real ones (`arms/placebo/<bucket>/`):
k neutral skills whose names and descriptions add up to the members' mean listing length (k = the
members' mean number of listed components); a SessionStart hook that prints neutral text of the
members' mean hook-plus-memory length; skill bodies of the members' mean body length. The split
between listing and injected text is the bucket mean, so in mixed buckets the mechanism is matched
approximately and the length exactly. Where every member installs as plain skills (mattpocock on
Codex), the placebo is installed as plain skills too.

**Token check before any task.** Characters are not tokens, and some skills hide entries from the
model (`disable-model-invocation`) that the character count includes. The pilot starts with one
trivial prompt per arm; the input tokens of the first request minus baseline give each arm's
always-on tokens. The bucketing rule is then re-applied to these token numbers, and every placebo
is rescaled to its bucket's mean in tokens, before any task trial. The final buckets and lengths are
recorded as an amendment.

Also fixed:

- The placebo text (`placebo/corpus.md`) describes the environment in neutral, descriptive wording
  and restates what the agent already knows (the task arrives in a message, files are in the working
  directory, commands return exit codes). It adds length and the presence of an instruction, but no
  new direction on process, verbosity, testing, planning or tool choice.
- It contains no words from the tested skills' names or trigger phrases.
- Token counts are reported next to character counts.
- The corpus is committed before the first run and never edited afterwards except through an
  amendment.

## 5. Harnesses and models

Research behind these choices: `docs/research/2026-09-25-harness-infra.md`.

| | Claude Code | Codex CLI |
|---|---|---|
| Version | 2.1.282 | 0.157.0 |
| Model | `claude-opus-5-5` | `gpt-6-sol` |
| Reasoning effort | Claude Code's default for this model: medium (code.claude.com/docs/en/model-config: "Opus 5.5 defaults to `medium`"), passed explicitly | Codex's default for this model: medium (`codex debug models`), passed explicitly |
| Permissions | `bypassPermissions` (Harbor default) | `--dangerously-bypass-approvals-and-sandbox` (Harbor default) |
| Plugin hooks | run (headless sessions trust the folder) | run: `--dangerously-bypass-hook-trust` in arms that install a plugin |
| Built-in web tools | disabled: `WebSearch`, `WebFetch` | disabled: `web_search = "disabled"` |
| Login | owner's Claude Max subscription via a dedicated long-lived token (`claude setup-token`) | owner's ChatGPT subscription via a separate Codex login (`codex login --device-auth` in its own `CODEX_HOME`) |

- Runner: Harbor 0.23.0 (`harbor-framework/harbor`), local Docker Desktop, native `linux/arm64`
  images, concurrency at most 2. One Harbor job per trial so that the order and the stop rules are
  controlled by `src/skill_placebo/runner.py`. Harbor is started with a clean environment: only the
  one harness's login, telemetry off. Agent classes: `src/skill_placebo/harbor_agents.py`.
- Agent timeout: the task's own, capped at 1,200 s. No turn limit, so that multi-step workflows are
  not cut short by the harness. A timeout is a failed trial.
- Opus 5.5 is the newest Claude model and what subscribers run in Claude Code; effort is the
  harness default, so the setup matches everyday use (owner's choice, 2026-09-28). `gpt-6-sol` is the
  model Codex documents for "complex coding and agentic workflows"
  (`learn.chatgpt.com/docs/models`, 2026-09-25). The effort value is passed explicitly, equal to the
  default, so that a change of defaults in a later release cannot change the setup; it is recorded
  in every trial.
- Web tools are off in every arm because the fixes for public benchmark tasks are on GitHub. The
  shell still has network access (the agent needs it to reach the model). Trials that fetch the
  upstream repository of a SWE-bench task are flagged in the data.
- **Identical file systems.** Every plugin directory is mounted read-only in every container of
  every arm; only an environment variable decides whether a plugin loads. Every arm gets the same
  marker files, so ponytail and caveman do not tell the agent to offer a statusline setup (they
  would in every fresh container), and i-have-adhd's documented always-on flag is present
  everywhere (only its own hook reads it). `SUPERPOWERS_DISABLE_TELEMETRY=1` in every arm.
- **Versions are frozen for a run.** Harness versions, model IDs, Harbor version, skill commits and
  image digests are pinned before the pilot and recorded in every trial's result. If a harness or
  skill releases an update during a run, the run finishes on the pinned version; the update is at
  most a later rerun.
- **Subscriptions, not API keys.** The owner chose to run on existing subscriptions. Nothing is
  billed per token, so every cost in this study is an **estimate from tokens**: recorded input,
  cache write, cache read and output tokens times the public API list price on 2026-09-25
  (`src/skill_placebo/collect.py`). The tables label it that way.

### 5.1 Scripted approval turn

superpowers (brainstorming "HARD-GATE") and, less strictly, karpathy-skills ("If uncertain, ask"),
agent-skills and mattpocock can stop and wait for the user. Their authors document no unattended
mode. In a headless run a stop would end the trial with nothing done, which is not how the skills
are used. So every arm of every harness gets the same simulated user:

- After the agent's run, if its final message has a `?` in its last 200 characters, the harness
  sends, in the same session: *"If you are waiting for approval to continue the task, you have it:
  proceed with your best judgment. If the task is complete, reply DONE."*
- At most 2 times per trial. The text and the rule never change.
- Implementation: `harbor_agents.py` (`CHECK_JS`, `APPROVAL_TEXT`); Claude Code continues with
  `--continue`, Codex with `codex exec resume --last`; tokens of approval turns count in the trial.
- The number of approval turns per trial is a secondary outcome. The results table marks
  superpowers (and any skill whose trials use approval turns) as **"scripted approval, not an
  author-documented mode"**.
- Check: if approval turns change the cost of the baseline or placebo arms by more than 5% (their
  share of those arms' total estimated cost), this is reported to the owner before the main run.

## 6. Tasks

Research: `docs/research/2026-09-25-task-pool.md`, `docs/research/2026-09-28-harder-tasks.md`.
SkillsBench is not used: about half of its tasks need domain knowledge that a general workflow skill
cannot supply, and several of its images ship skills that would leak into the control arms.

- **Candidate pool: 40 tasks** with deterministic test-based verifiers, no LLM judges, vendored at
  pinned upstream commits in `tasks/pool/` (`manifest.json`, `PATCHES.md`):
  - 20 SWE-bench Verified (real bug fixes and small features in django, sympy, pytest, pylint,
    seaborn): 14 where 2-4 of 6 frontier-model runs pass, 6 harder ones where 1-2 of 6 pass, because
    Opus 5.5 is stronger than the models with public per-task data. Images: Epoch's arm64 builds,
    pinned by digest.
  - 12 Terminal-Bench 2.1 (scripting, parsing, build, performance, compression, data processing),
    built from their own Dockerfiles.
  - 8 OpenThoughts-TBLite (bug fixes and features in small Python services and CLIs).
- Patches are identical for every arm: base image for arm64; agent timeout cap; for SWE-bench, the
  grading script's own dependencies (a Python >= 3.11 and swebench, datasets, fastcore at the
  versions the script pins) are installed into the image at build time, because the unpatched
  grader downloads them after the agent has finished and a network stall there hung a grading run
  for 20 minutes. Nothing in any instruction, test or solution is changed. Base images that
  Docker Hub throttled were taken from its official mirror `mirror.gcr.io`
  (`tasks/pool/BASE_IMAGES.txt`).
- **Oracle check:** before the pilot every pool task runs its reference solution 2 times on the
  runner; a task that does not pass both times leaves the pool (`tasks/pool/ORACLE.md`).
- **Selection** (Claude Code baseline arm, in the pilot):
  1. Every pool task runs 2 times. Tasks with 1 of 2 passes qualify.
  2. If fewer than 20 qualify, tasks at 0/2 or 2/2 get a third trial, in the seeded order, while the
     pilot cap allows; 1/3 and 2/3 qualify.
  3. If more than 20 qualify, 20 are drawn with seed 20260928, keeping the source mix as close to
     the pool's as possible (20:12:8).
  4. If fewer than 15 qualify, the set is filled to 15 with tasks that passed every pilot trial, in
     the seeded order. They carry no pass-rate information but still measure cost; they are flagged.
     With Opus 5.5 many tasks may sit at the ceiling; the headline rests on cost, so this is
     acceptable.
- The candidate list, seed and pilot results are committed before the main run.
- **Pilot runs are not reused as main-run data.** Selecting tasks on baseline results and then
  reusing those results would bias the baseline (regression to the mean). The main run repeats the
  baseline from scratch.
- The same tasks are used on both harnesses. The Codex baseline pass rate is reported as observed,
  even if it falls outside 30-70%.
- Tasks are public and may be in model training data (section 13).

## 7. Procedure

- N = 5 trials per task per arm per harness in the full design (section 11.3 for the reduced ones).
- Order: trials are interleaved in randomized blocks (one block = every arm on every task once), so
  that drift in model serving over the run window affects all arms equally. The seed is committed.
- Infrastructure failures (container did not start, agent install timed out, verifier crashed, API
  5xx before the agent's first action) are retried up to 2 times and logged. Agent failures
  (timeout, gave up, broke the environment, stopped after the last approval turn) are not retried:
  they count as failed trials and their cost counts.
- A limit warning, a rate-limit error or an authentication failure stops the whole batch (section
  12); the interrupted trial is rerun after the stop is cleared.
- Every trial is kept, including failed and aborted ones, with the reason.

## 8. Outcomes

Primary, per trial:

1. **Cost** in USD, computed from recorded token usage (input, cache write, cache read, output) at
   the provider's list prices on the run date. The price table is committed with the results.
2. **Pass**: verifier reward = 1.

Secondary: tokens by type; turns; tool calls; wall time; USD per solved task (total cost / trials
passed); size of the final diff; approval turns (5.1); whether the skill fired (Skill tool calls,
hook output in the session log).

## 9. Analysis

All comparisons are within one harness and paired by task.

- **Cost ratio** R = mean cost (skill) / mean cost (placebo). **Pass difference** D = pass rate
  (skill) - pass rate (placebo), in percentage points.
- 95% confidence intervals by cluster bootstrap over tasks: resample tasks with replacement (the
  same tasks for both arms), keep all trials of each resampled task, 10,000 resamples, seed
  20260925. Two-sided p-values from the same bootstrap distribution. Implementation:
  `src/skill_placebo/analysis.py`, committed before any data.
- Multiple comparisons: Holm correction across the skills run on a harness (9 or 6), separately per harness and per
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

The pilot is capped at 150 runs per harness and runs with concurrency 2.

### 11.1 Claude Code (at most 150 runs)

- Token check (section 4.1): one trivial prompt per arm, 15 runs (baseline, 5 placebos, 9 skills).
- Task selection (section 6): 40 pool tasks x 2 baseline trials = 80, plus at most 5 third trials.
- Kill test: caveman, ponytail and i-have-adhd with their placebos cc-5 and cc-4 (5 arms), on 5
  tasks drawn from the pool with seed 20260928 before the pilot (3 SWE-bench, 1 TB2.1, 1 TBLite),
  2 trials each = 50. These three put the most always-on text into the context without an
  interactive gate, so they are the likeliest to move cost if anything does.

### 11.2 Codex (at most 100 runs)

- Token check: one trivial prompt per Codex arm, 11 runs (baseline, 4 placebos, 6 skills).
- 40 pool tasks x 1 baseline trial: checks that every task runs under Codex and gives a first base
  rate.
- Kill test: ponytail, agent-skills and compound-engineering with their placebo cx-4 (4 arms), on
  the same 5 tasks, 2 trials each = 40.

### 11.3 Kill rule and the size of the main run

- **Kill rule.** If no skill on either harness shows a non-trivial cost difference vs its placebo,
  the project stops at a write-up without a repo release. Non-trivial means a point estimate of R
  outside 0.90-1.10 **and** a 95% CI that excludes 1. With 5 tasks the CI is wide; the gate only
  asks whether anything moves at all.
- **Designs** (arms counted with the buckets of section 4.1; the token check may change the number
  of placebos slightly):

  | Design | Skills (priority order, section 3) | Tasks | N | Claude Code runs | Codex runs |
  |---|---|---|---|---:|---:|
  | Full | all 9 | 20 | 5 | 15 arms x 100 = 1,500 | 11 arms x 100 = 1,100 |
  | Reduced | first 8 (drops compound-engineering) | first 15 of the selected set, seeded order | 3 | 14 x 45 = 630 | 10 x 45 = 450 |
  | Minimal | first 6 (also drops planning-with-files, i-have-adhd) | 15 | 3 | 12 x 45 = 540 | 8 x 45 = 360 |

- **Choice of design, from resource numbers only, never from effect estimates** (maintainers'
  decision, 2026-09-28). For each harness, `U` = the share of that plan's weekly limit the pilot used,
  scaled to 150 runs:
  - `U <= 3%`: **Full**, spread up to 2026-10-09 across the plan's weekly reset;
  - `3% < U <= 6%`: **Reduced**;
  - `U > 6%`: **Minimal**.

  A design is also dropped a step if its runs cannot finish by 2026-10-09 09:00 UTC at the pilot's
  mean wall time per run with concurrency 2, keeping 12 hours of reserve. If even the minimal design
  does not fit, that harness runs it on as many of the 15 tasks as fit, in the seeded order, and the
  gap is reported; fewer than 10 tasks drops the harness and the owner is asked. The 25% stop rule of
  section 12 holds throughout. The choice and the numbers behind it are recorded as an amendment
  before the main run.
- Pilot trials are not reused in the main analysis. The pilot's own numbers are published
  separately.

## 12. Budget and stop rules

Runs use the owner's subscriptions, whose weekly limits are shared with the owner's other work. The
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
- After publication, anyone can open an issue about how a skill was installed or about its placebo
  (template: `.github/ISSUE_TEMPLATE/skill-install-dispute.yml`); every trial's records are public, so an
  issue can point at the exact runs. A confirmed installation error means that skill's arms are rerun in
  full, the result is updated, an amendment records it, and the issue is linked from the results page.
- Neutral wording. The results say what was measured, on which tasks and models, and nothing about
  intent.

## 15. Reproduction and data release

- One command reproduces a skill's row: `uvx skill-placebo run <owner/repo>`; its exact flags are
  documented in the README when the CLI ships (it wraps the runner used here).
- Raw trajectories, verifier outputs, token usage and the analysis notebook are published.
- Before release every artifact passes `scripts/scrub.py --check`: no API keys, no local paths,
  no personal e-mail.

## 16. Amendments

### Amendment 1 (2026-09-29, before any benchmark run): how subscription use is measured

**Reason.** The owner uses Claude Code for other projects in parallel, so the change in the plan's
usage page between "before" and "after" a batch mixes the benchmark with other work and cannot
measure the benchmark's share (owner, 2026-09-29).

**Change** (replaces the measurement in sections 11.3 and 12; the thresholds themselves are unchanged):

1. The benchmark's use is the sum over its trials of the tokens recorded in each trial's session
   logs inside the containers (input, cache write, cache read, output), converted to a $ equivalent
   at public API list prices (`claude-opus-5-5`, `gpt-6-sol`). The runner appends every trial to
   `jobs/ledger-<harness>.jsonl` and keeps the running total. This is the same token-based cost
   estimate that is already a secondary outcome.
2. The maintainers convert $ to a share of the weekly limit: the owner gives one reading of the plan's usage
   page (% of the week and the reset time); the maintainers compute the owner's local Claude Code use since
   that reset from the session logs on this machine at the same prices; their ratio is "% of the
   week per $". Same model (Opus 5.5), so the ratio carries over. It is conservative: use on other
   machines is not in the local logs, so the ratio overstates the share per $.
3. The 25% stop rule and the design thresholds of section 11.3 are applied to this estimate. The
   runner stops a batch when the ledger's $ equivalent since the weekly reset exceeds the $
   threshold the maintainers derive from 25%; it refuses to run without one.
4. Codex: the weekly `used_percent` from Codex's own rate-limit events is used as before when the
   owner does not use Codex in parallel; otherwise the same token method applies. Both stops are
   active.

**Runs affected:** all (no run has happened yet).

### Amendment 2 (2026-09-29, before any benchmark run): limit units, pace and checkpoints

**Reason.** The maintainers calibrated the owner's Claude plan against the owner's own session logs in *units*
rather than dollars, so the benchmark must be metered in the same units (2026-09-29: one
reading of the usage page, Max 20x, 4% of the week used, reset Mon 2026-10-05 10:00 UTC).

**Change** (refines amendment 1; the $ equivalent stays as the cost outcome of section 8):

1. **Units** per trial = uncached input x 1 + cache write x 1.25 + cache read x 0.1 + output x 5,
   in tokens (`collect.units_from_tokens`), the same formula the maintainers applied to the owner's logs.
   The runner logs units per trial and in total per limit week.
2. **Claude Code stop:** 145 million units in the limit week (the maintainers' conservative translation of
   25%), or any limit warning, rate-limit error or authentication failure.
3. **Claude Code pace:** no trial starts while the trailing 5 hours hold 75 million units or more
   (about 40% of a 5-hour window), so the owner keeps room for other work; the runner waits.
4. **Design thresholds of section 11.3 in units**, scaled to 150 pilot runs: at most 17 million
   units (about 3% of the week) → Full; 17-35 million → Reduced; more → Minimal.
5. **Checkpoint:** after the first 10 task trials the runner stops and the median and maximum units
   per trial go to the maintainers before the pilot continues.
6. **Codex** (owner, 2026-09-29: ChatGPT Plus, weekly limit 12% used, no parallel Codex use): the
   weekly `used_percent` from Codex's own rate-limit events is the measure; stop at +25 percentage
   points over 12%; pause while the 5-hour window is 40% full or more. Units are logged too.
7. Before the main run the owner gives a new usage reading and the maintainers recalculate the ratio.

**Runs affected:** all (no run has happened yet).

### Amendment 3 (2026-09-29, after the first calibration run, before any task trial): plan windows as the main guard

**Reason.** Claude Code writes a `rate_limit_event` into its stream in every run. Its status
"allowed" is informational; the runner first read it as a limit signal and stopped after one
calibration run (a false stop; no trial was lost). The same event carries the plan's own
utilization of the 5-hour and 7-day windows for the whole account (`unifiedWindows`), which
matched the owner's usage page (13% and 4%).

**Change** (adds to amendment 2):

1. A limit stop is a `rate_limit_event` whose status is not "allowed", or that reports overage use;
   plus the rate-limit errors and authentication failures of section 12.
2. Main guard for Claude Code, from the last event of each trial: stop when the 7-day utilization
   reaches its value before the pilot + 0.25 (0.04 → 0.29) or 0.80 absolute; pause until the
   5-hour window resets when its utilization is 0.80 or more (the stricter of the two values
   discussed; 2026-09-29). This counts all of the owner's use,
   so it is conservative.
3. The units and $-equivalent ledger stays: it attributes use to the benchmark and carries the
   design thresholds (2026-09-29: at most $45 / $90 per 150 pilot runs, and 17 / 35 million
   units; the stricter decides). The weekly $370 and 145-million-unit stops stay as second guards.
4. The ledger records the 5-hour and 7-day utilization after every trial.
5. A regression test pins that an "allowed" event never stops a batch.
6. Codex (ChatGPT Plus): stop at +25 points over the weekly percentage before the pilot or at 80%
   absolute; pause at 40% of the 5-hour window. If the first Codex trials show that the planned 90
   runs cannot fit, the Codex pilot is cut to its kill test and the gap is reported as a limitation.

**Runs affected:** the calibration runs of step 1 and everything after (no task trial yet).

### Amendment 4 (2026-09-29, before any task trial): final Claude Code placebo buckets, from tokens

As pre-registered in section 4.1, the bucketing rule was re-applied to measured tokens and the
placebos rescaled before any task trial (`results/pilot/token-check-claude-code.json`,
`results/pilot/token-recheck-claude-code.json`).

Always-on tokens over the baseline's first request (14,916 tokens), one trivial run per arm:

| Placebo | Members (tokens) | Placebo tokens (measured) | Largest deviation |
|---|---|---:|---:|
| cc-1 | planning-with-files (666) | 663 | -0.5% |
| cc-2 | mattpocock (906), karpathy (986) | 939 | -4.8% |
| cc-3 | superpowers (2,168), compound-engineering (2,383), i-have-adhd (2,473) | 2,347 | +8.3% |
| cc-4 | ponytail (2,854) | 2,874 | +0.7% |
| cc-5 | agent-skills (3,751), caveman (3,917) | 3,800 | -3.0% |

The character-based buckets of section 4.1 are superseded for Claude Code. The placebos were
rebuilt with the same generator, sized by a token model fitted on the first five placebos
(tokens ≈ 0.271 x listing characters + 0.264 x hook characters + 12 x listed entries; residuals at
most 7 tokens), then measured. Codex buckets get the same treatment in the Codex token check.

Calibration cost: 21 trivial runs (16 in the first pass, one of them a duplicate started by a
resume while a stopped process was still waiting; 5 in the recheck, one retried after an agent
install timeout). Plan windows unchanged by it (5-hour 13-14%, 7-day 4%).

### Amendment 5 (2026-09-29, before the kill test): what counts toward the pilot cap

**Reason** (resource, not effect): the pilot cap of 150 runs per harness protects the owner's
subscription limits. The 21 calibration runs of section 4.1 (trivial one-line prompts) used about
0.2 million units ($0.6 equivalent) and did not move the plan's windows; infrastructure retries
happen before the agent works and use close to nothing. Counting them would cut the kill test.

**Change:** the cap of 150 (Claude Code) and 100 (Codex) counts task trials only (selection,
third trials, kill test), one per trial however many infrastructure attempts it needed.
Calibration runs and infrastructure retries are excluded from the cap but stay in the ledger:
every attempt is logged with its attempt number and an infrastructure-failure flag, and its tokens
count in the attribution of use to the benchmark and in every stop rule. Decided by the maintainers,
2026-09-29.

**Runs affected:** the selection step (in progress; its first trials are unaffected) and the kill
test.

### Amendment 6 (2026-09-29, after the selection step, before the kill test): harder tasks added

**Reason.** Claude Code with Opus 5.5 at medium effort passed 77 of 78 baseline selection trials:
38 of 39 pool tasks at 2/2, one (application-debug) at 1/2. Only one task qualified for the
30-70% band, far below 20. As agreed by the maintainers before the selection step finished (2026-09-29),
the pool is topped up with harder tasks; the rule "tasks are selected on baseline results only"
is unchanged, and no skill or placebo arm had run on any task.

**Change.**
1. Eight harder candidates join the pool, chosen from external data only
   (`docs/research/2026-09-29-harder-tasks-2.md`): SWE-bench Verified django-11141, django-11734,
   django-13512, django-14140, django-16256, sphinx-10435, sympy-17630 (0-1 of 6 frontier runs, and
   the frontier failures read as genuine rather than tests that go beyond the issue text), and
   Terminal-Bench 2.1 video-processing (upstream timeout 3,600 s, capped at 1,200 s like every
   task). All eight pass the oracle 2/2; make-doom-for-mips was staged and failed the oracle, so it
   stays out (`tasks/pool-extra/ORACLE.md`).
2. They get the same selection: 2 baseline trials each (16).
3. The at most 5 third trials of section 11.1 go to tasks at 0/2 or 2/2 in the seeded order, taken
   round-robin over the sources (SWE-bench, Terminal-Bench 2.1, TBLite).
4. Selection then follows section 6 rules 3-4 over the 48-task pool. If fewer than 15 tasks qualify,
   the set is filled to 15 with tasks that passed every trial, in the seeded order, flagged
   "ceiling". The headline stays on cost; pass rate is reported with its CI and the ceiling is
   listed as a limitation (2026-09-29).

Pilot task trials on Claude Code after this: 78 + 16 + 5 + 50 (kill test) = 149 of 150.

**Runs affected:** the added selection trials, third trials, kill test and main run.

### Amendment 7 (2026-09-29, before the kill test): kill-test arms follow the token buckets; cap 160

**Reason.** Section 11.1 lists the Claude Code kill test as caveman, ponytail and i-have-adhd with
placebos cc-5 and cc-4 (5 arms). It was written before the token check. Under amendment 4,
i-have-adhd's placebo is cc-3, so the three skills have three placebos and the kill test has 6 arms:
6 x 5 tasks x 2 = 60 trials. With 99 task trials already run, that is 159, above the pilot cap of 150.

**Change.** The kill-test arms follow the buckets of amendment 4: skill-caveman, skill-ponytail,
skill-i-have-adhd, placebo-cc-5, placebo-cc-4, placebo-cc-3. The five tasks drawn before the pilot
stay unchanged (django-15957, pytest-7490, django-11265, largest-eigenval, fix_async_worker_queue).
The Claude Code pilot cap rises to 160 task trials (maintainers' decision, 2026-09-29): the cap was a
resource guard set before cost was known; measured cost is about 0.8 percentage points of the week
per 78 trials, so 9 more trials are about 0.1 points ($1.6 equivalent). Dropping a pre-drawn task or
arm would change the method to save that. The real guards are unchanged: stop at 7-day utilization
0.29 or 0.80, pause at 5-hour 0.80.

**Runs affected:** the Claude Code kill test.

### Amendment 8 (2026-09-29, before any Codex task trial): final Codex placebo buckets, from tokens

Codex token check (`results/pilot/token-check-codex.json`): the baseline's first request is 11,232
tokens; always-on tokens over it: planning-with-files 171, mattpocock 657 (as on Claude Code, the
`disable-model-invocation` skills are not shown to the model), superpowers 791 (no hook on Codex),
compound-engineering 1,883, ponytail 2,043, agent-skills 2,312. The Codex week stayed at 12%.

Three placebo plugins at first failed to install: their marketplace pointed at `"url": "./"`, which
Codex clones with git, and placebo directories are not repositories; the source is now
`{"source": "local", "path": "./"}`. The runner now treats "the arm's plugin or memory file did not
reach the agent" as an infrastructure failure and retries (checked for every past trial).

Re-bucketing by the rule on tokens gives five Codex buckets. A token model fitted across install
mechanisms did not predict well (entries listed from a plugin and from `~/.agents/skills` cost
differently), so each placebo was sized from the measured placebo of the same mechanism and
measured again (`placebo/codex_plan.json`, `results/pilot/token-recheck-codex.json`):

| Placebo | Members (tokens) | Placebo tokens (measured) | Largest deviation | Iterations |
|---|---|---:|---:|---:|
| cx-1 | planning-with-files (171) | 175 | +2.3% | 0 (kept) |
| cx-2 | mattpocock (657), installed as plain skills like mattpocock | 631 | -4.0% | 1 |
| cx-3 | superpowers (791) | 822 | +3.9% | 1 |
| cx-4 | compound-engineering (1,883), ponytail (2,043) | 1,995 | +5.9% | 1 |
| cx-5 | agent-skills (2,312) | 2,250 | -2.7% | 2 |

**Codex kill test** (section 11.2): ponytail, agent-skills and compound-engineering with their
placebos cx-4 and cx-5 (5 arms) on the same 5 pre-drawn tasks, 2 trials each = 50. Codex selection
covers the 47 pool tasks that passed the oracle, 1 trial each. 47 + 50 = 97 task trials, within the
Codex cap of 100.


### Amendment 9 (2026-09-30, after the pilot, before any main-run trial): main-run design, guards, verifier timeouts, Codex

Decided by the maintainers on 2026-09-30, from the pilot's resource numbers
(`results/pilot/SUMMARY.md`); no effect estimate enters the choice.

**1. Claude Code: full design.** 9 skills, the 15 selected tasks (`tasks/selected.json`), N = 5:
15 arms x 75 = 1,125 trials in 5 randomized blocks, seed 20260930 (`scripts/main.py`). The pilot's
resource share per 150 runs was below the 3% threshold (9.1 million units, $30). At the pilot's mean
wall time per trial (4.5 minutes, 164 trials) the design needs about 42 hours at concurrency 2 and
fits the 2026-10-09 deadline with the 12-hour reserve. The run may cross the plan's weekly reset
(Mon 2026-10-05 10:00 UTC). Guards (replacing those of amendments 2-3 for the main run):
- **Main stop: the benchmark's own use by the ledger**, at most 25 points of the plan's week per limit
  week, at the maintainers' calibration of 1 point ≈ 5.8 million units: 145 million units. It counts every
  benchmark run logged in that limit week (the pilot included) and follows the reset time that Claude
  Code reports. The $370-per-week equivalent of amendment 3 stays as a second guard.
- **Account 7-day window at 0.80 or more: pause, not stop**, so that the owner keeps room for other
  work. The pause lasts until the weekly reset or one hour, whichever comes first; the next trial
  reads the window again (at most 2 trials per hour while it stays at 0.80, at concurrency 2).
- **Account 5-hour window at 0.80 or more: pause** until it resets, as before. The trailing-5-hour
  pace of amendment 2 (75 million units, $200) is unchanged.
- The pilot's stop at +25 points of the account's 7-day window does not apply: the account window
  mixes the owner's other work (amendment 1); the ledger measures the benchmark itself.
- Limit, rate-limit and authentication error events stop the batch, as before. Concurrency 2.

**2. Verifier timeouts.** A verifier timeout can come from the agent (its code hangs the tests) or
from the machine (load, a slow network during grading). Rule, for every run from now on: when a
trial's verifier times out, the verifier runs once more, with the same tests and timeout and no
agent, on the agent's final state. If it finishes within the timeout, its reward is the trial's
result and the episode is flagged as infrastructure (`verifier_rerun` in the data); another timeout
leaves a failed trial, as before. A rerun that cannot start for infrastructure reasons is repeated up
to 2 times, like any infrastructure failure (section 7).
- The final state is a snapshot: right before the first verification starts, outside the agent's
  and the verifier's timeouts, the container is committed to a local image
  (`skill_placebo.harbor_launch`); the rerun starts a fresh container from it. Only the file system
  is kept, not processes the agent left running. Snapshots are deleted after each trial. Checked end
  to end with a test task whose first verification leaves a marker (absent from the snapshot, so the
  snapshot precedes verification) and times out: one variant passed on the rerun, one timed out again.
  A commit took 0.2-0.6 seconds there.
- **Applied to the pilot retroactively.** One pilot trial had a verifier timeout (Claude Code kill
  test, placebo-cc-4 x fix_async_worker_queue, 180 seconds; the verifier's output was empty, so it
  stalled while installing its own tools; this task's verifier otherwise took a median 18 seconds
  over 26 runs). Its container no longer existed, so its final state was reconstructed: the task
  image, the packages Claude Code's setup installs, and the agent's 4 shell commands replayed in order
  from its session log (the agent changed files only through Bash; `scripts/pilot_verifier_rerun.py`).
  The rerun passed 11 of 11 tests in 16 seconds; as a control, the same task without the agent's
  changes fails 5 of 11. The pilot table changes only there: placebo-cc-4 passes 10 of 10 (was 9 of
  10); ponytail vs cc-4 D = 0 (was +10 points); R and its CI are unchanged (0.75 [0.63, 0.88]); the
  kill rule's result is unchanged. No other pilot trial had a verifier timeout.

**3. Codex.** Codex is not in the main run: at the pilot's rate even the minimal design needs about
76 points of the Plus week (section 11.3). The Codex pilot is published as a secondary result with
its actual n. After the Codex weekly reset (about 2026-10-04), a Codex top-up runs within +25 points
of that week (the first trial's reading is the start value; stop at +25 points or 80% absolute; pause
at 40% of the 5-hour window): ponytail, agent-skills and compound-engineering with placebos cx-4 and
cx-5 (5 arms, no baseline), on the selected tasks in their seeded order without those where Codex's
baseline selection trial failed (the floor: application-debug, sympy-17630, extract-elf,
seaborn-3069), the first 10 of them, N = 2 in 2 randomized blocks, seed 20260930: 100 trials. If the
limit stops it early, the completed block is balanced and the partial one is reported as is. If the
owner buys ChatGPT Pro, Codex is extended by a separate amendment.

**4. Pilot guards.** The pilot cap of 160 task trials (amendment 7) and the Codex stop at +25 points
(amendments 2-3) were pilot guards. Pilot data do not enter the main run (section 11.3).

**Runs affected:** the main run, the Codex top-up, and the pilot's one verifier-timeout trial.

### Amendment 10 (2026-09-30, during the main run, before the Codex top-up): newer Codex and model, pins kept and enforced

**Note on the Codex model** (2026-09-30, checked against the sources). Section 5 chose
`gpt-6-sol` as the model Codex documented for "complex coding and agentic workflows"
(learn.chatgpt.com/docs/models, 2026-09-25). After this method was registered, GPT-6.1 Sol appeared:
Codex CLI 0.159.1 (2026-09-29) made it the default in the bundled catalog (release notes, #49323),
and the models page now reads "For complex coding and agentic workflows, use GPT-6.1 Sol when
available to your account and client". `gpt-6-sol` is still listed there. The study keeps
`gpt-6-sol`, so that the Codex top-up is comparable with the Codex pilot; results are for that model
(section 13).

**Harness versions stay pinned.** Codex CLI 0.158.0-0.159.2 (2026-09-28/29) changed plugin loading
(#47858, #47939, #48035), skill catalogs (#48353) and removed the bundled `plugin-creator` skill
(#48604), which would change the baseline arm's catalog. The top-up stays on Codex CLI 0.157.0 with
`gpt-6-sol` at medium, like the pilot. Each trial installs the exact version (`npm install -g
@openai/codex@0.157.0`, Claude Code 2.1.282 likewise) and passes the model explicitly, so neither
a new release nor a new default reaches the containers. Checked in the session logs of every trial so
far: 114 Codex sessions report CLI 0.157.0, gpt-6-sol, effort medium; every Claude Code session of the
pilot and of the main run reports 2.1.282 and claude-opus-5-5.

**Enforced from now on:** after each trial the runner compares the CLI version and model that the
agent's own session logs report with the pins and stops the batch on any difference
(`runner.pin_mismatch`); the version and model go into every trial's row. For the main run this takes
effect when the runner restarts at the report checkpoint (about trial 375); the trials before it
were checked the same way afterwards.

**Runs affected:** the Codex top-up; the main run from its checkpoint (a guard, the design is unchanged).

### Amendment 11 (2026-09-30, before any Codex top-up trial): Codex top-up to N = 4 in two quota batches

Decided by the maintainers on 2026-09-30, before any top-up data, so that no stop can depend on
results.

1. The Codex top-up of amendment 9 grows to N = 4: the same 5 arms and 10 tasks, 4 randomized blocks
   with seed 20260930 (blocks 0-1 are exactly the N = 2 plan of amendment 9), in two batches of N = 2:
   batch 1 = blocks 0-1, batch 2 = blocks 2-3, one batch per Codex weekly quota. Each batch starts from a
   probe (one trivial Codex run) that reads the weekly window; a quota counts as fresh when the probe
   reads about 0-2%. Each batch stops at +25 points over its probe's reading or 80% absolute, and pauses
   at 40% of the 5-hour window.
2. Batch 2 runs whatever batch 1 shows, if it can finish by 2026-10-08 inclusive. If it cannot, the
   analysis uses N = 2 (batch 1) and says so. A batch cut short by its stop rule is reported as is.
3. While the Claude Code main run is going, Codex runs alongside only with concurrency 1, only if the
   Docker VM keeps at least 2 GiB of memory available next to the two Claude Code containers and the
   host has at least 15 GiB of free disk, and it is paused if the per-task median wall time of Claude
   Code trials rises by more than 20%. The Claude Code run has priority.
4. Versions stay Codex CLI 0.157.0 with gpt-6-sol at medium, checked after every trial (amendment 10).

**Observed at registration.** The owner reported on 2026-09-30 that the Codex weekly limits had been
reset early. A probe at 01:54 UTC read the weekly window at 37% (the pilot's end value) with the reset
still at 2026-10-04 00:41 UTC, so no fresh quota was confirmed and no top-up trial ran. With weekly
resets on 2026-10-04 and 2026-10-11, only batch 1 fits before 2026-10-08; batch 2 runs only if an earlier
fresh quota is confirmed by a probe.

**Runs affected:** the Codex top-up.

### Amendment 12 (2026-09-30, during the main run, before any analysis and before the change is switched on): size of the final diff

**Reason.** Section 8 lists the size of the final diff as a secondary outcome, and it is the quantity
closest to one README claim (ponytail, "~54% less code"). It was not collected: Harbor's SWE-bench
verifier prints the test patch, not the agent's changes, and every container is removed after its trial.
Found on 2026-09-30 while preparing the claims table; decided by the maintainers the same day.

**Change.**
1. **(a) Exact measure on the SWE-bench subset (7 of 15 tasks), from the moment it is switched on.**
   Right before verification, in the same hook as the snapshot (amendment 9), read-only commands in the
   container: `git diff --numstat` of the working tree against the task's base commit (the commit its
   verifier checks out), plus the line count of untracked files (`git ls-files --others
   --exclude-standard`, `wc -l`), with `GIT_OPTIONAL_LOCKS=0` so that git writes nothing. No `git add`,
   no index change: the verifier applies its test patch to this repository afterwards. For the other
   tasks, `docker diff` (paths added, changed, deleted) is logged as an exploratory record only and does
   not enter the claims table. A failure of this step is written to the trial's record; it neither fails
   the trial nor causes an infrastructure retry.
2. **(b) Exploratory measure for every trial: lines written by the agent's edit tools** (Claude Code's
   Edit, MultiEdit, Write and NotebookEdit calls that succeeded, from the session log): lines written and
   lines replaced. Edits made through shell commands are not seen, so (b) is not the final diff and is
   labelled that way wherever it appears.
3. Trials that ran before (a) was switched on have no (a) record. Blocks are randomized, so which trials
   miss it depends on time, not on arm. The number is recorded in the log when (a) is switched on.
4. The claims table compares ponytail's "~54% less code" with (a) only, on the SWE-bench subset, with its
   n shown; if n is small, the table says so. (b) appears as an exploratory column.

**Runs affected:** the main run from the moment (a) is switched on (the design is unchanged); the analysis.

### Amendment 13 (2026-09-30, during the main run, before any analysis): concurrency 3; Codex decoupled from the launch date

Decided by the maintainers on 2026-09-30 (the owner wants an earlier launch, tentatively
2026-10-06). Resource and schedule reasons only; no result has been looked at.

1. **Concurrency 3 instead of 2** for the rest of the Claude Code main run, while three conditions hold:
   the Docker VM keeps at least 1.5 GiB of memory available with three trial containers; the host has at
   least 15 GiB of free disk; the median trial wall time, normalized per task against the trials before
   the switch, rises by no more than 30%. If any fails, the runner goes back to 2 (a watchdog writes the
   wanted number into the batch's `CONCURRENCY` file; the runner reads it whenever a slot frees, so no
   restart and no trial is lost). All other guards are unchanged, including the pause at 80% of the
   5-hour window. The switch time and any change back are recorded in the log.
2. **Effect on the analysis.** Cost, tokens and pass rate do not depend on local load. Wall time (a
   secondary outcome) does. Blocks are randomized, so every arm meets both load levels in the same
   proportion; wall-time comparisons are additionally adjusted for the period (before or after each
   switch), and the switch times are reported with them.
3. **Codex is decoupled from the launch.** The launch publishes the Claude Code main run as the result and
   the Codex pilot as a secondary result with its actual n. The Codex top-up (amendment 11) runs after
   the 2026-10-04 reset; its results come out as an update 2-3 days after the launch (README and a
   "Codex results" post). Nothing about the top-up's design changes.

**Runs affected:** the main run from the switch; the Codex top-up's publication.

### Amendment 14 (2026-09-30, during the main run, before any analysis): a missing reward file gets the same single rerun

**Reason** (2026-09-30). A trial whose verifier leaves no reward file (`RewardFileNotFoundError`) can
mean that the agent broke the environment (an agent failure) or that the verifier itself failed
(infrastructure). Counting it always as a failed trial would be wrong half the time, and so would
counting it always as infrastructure.

**Change.** It is handled exactly like a verifier timeout under amendment 9: the verifier runs once more,
with the same tests and timeout and no agent, in a fresh container from the snapshot taken before the
first verification. If the rerun writes a reward, that reward is the trial's result and the episode is
flagged as infrastructure (`verifier_rerun` in the data); if the reward file is missing again (or the rerun
times out), it is a failed trial. Checked end to end without a model: a task whose first verification left
no reward file and whose rerun wrote one gave reward 1; a task that never wrote one stayed a failed trial.

**Retroactive.** No pilot or main-run trial so far has had `RewardFileNotFoundError` (0 of all trials up to
the switch-on, whose time is in the log), so nothing changes in past data.

**Runs affected:** the main run from the runner restart that switches it on; the Codex top-up.

### Amendment 15 (2026-09-30, before any Codex main-run trial): Codex runs the minimal design; the owner lifts the Codex budget stop

**Reason.** The owner (2026-09-30): the whole Codex weekly quota may be used. No Codex data from the top-up exists yet; this is decided before
any.

**Change** (replaces the Codex top-up of amendments 9 and 11):
1. **Design: the pre-registered minimal design of section 11.3**, counted with the final Codex buckets of
   amendment 8. The minimal design keeps the first 6 skills by priority; of those, 4 run on Codex
   (superpowers, mattpocock, ponytail, agent-skills; karpathy and caveman are not run on Codex, section 3).
   Arms: baseline, the 4 skills and their placebos cx-2, cx-3, cx-4, cx-5 = 9 arms (section 11.3's "8 arms"
   was counted with the character buckets, before amendment 8). Tasks: the 15 selected tasks without the 4
   where Codex's baseline selection trial failed (application-debug, sympy-17630, extract-elf,
   seaborn-3069) = 11 tasks. N = 3 in 3 randomized blocks, seed 20260930: 9 x 11 x 3 = 297 trials.
2. **Guards.** The +25-point stop on the Codex week is lifted by the owner. Pause (not stop) while the
   weekly window is at 95% or more, until its reset (2026-10-04 00:41 UTC); pause while the 5-hour window is
   at 90% or more, until it resets. Limit, rate-limit and authentication error events still stop the batch.
   Versions: Codex CLI 0.157.0, gpt-6-sol, medium, checked after every trial (amendment 10).
3. **Priority to Claude Code.** Codex runs alongside the Claude Code main run with concurrency 1 only while
   the Docker VM keeps at least 1.5 GiB of memory available, the host at least 15 GiB of free disk, and the
   per-task median wall time of Claude Code trials stays within +30% of its level before Codex started;
   otherwise Codex pauses until the Claude Code run ends, then runs with concurrency 2-3.
4. **Publication.** If the Codex run finishes by 2026-10-04 15:00 UTC, its results go into the 2026-10-06
   launch; otherwise they come out as an update (amendment 13). The maintainers decide on 2026-10-04 from the
   runner's report. The analysis is the pre-registered one (section 9), Holm across the 4 Codex skills.

**Expected use** (pilot rate, 0.21-0.26 points of the Plus week per trial): about 62-77 points for 297
trials. The week was at 37% on 2026-09-30, so about 225-275 trials fit before the 95% pause and the rest
run after the 2026-10-04 reset.

**Runs affected:** Codex main run (replaces the top-up; no top-up trial has run).

### Amendment 16 (2026-09-30, during the main run, before the block boundary it sets and before any look at outcomes): v1 volume

**Decision.** The owner, 2026-09-30 about 11:00 UTC: better to test the main skills and release early than to
spend several more days on this many skills (paraphrased). The maintainers turned it into the
rule below. It is made blind: no one (the owner, the maintainers, the runner's agent) had looked at main-run outcomes by arm.
Only resource and process counts had been reported (trials done, infrastructure failures, plan windows,
disk).

**Change.**
1. **Claude Code stops at the block boundary after block 3**: blocks 0-2 of the randomized N = 5 plan, so
   N = 3 per task and arm, 15 arms x 15 tasks x 3 = 675 trials. All 9 skills stay: blocks are shuffled over
   every arm and task, so every arm has the same N at a block boundary and dropping skills now would save
   nothing. Blocks 3-4 are not run for v1.
2. **Codex runs N = 2** instead of 3 (amendment 15): 9 arms x 11 tasks x 2 = 198 trials, blocks 0-1 of the
   same seeded plan. It starts as soon as the Claude Code run stops; its guards are unchanged.
3. **Publication.** The results are published as v1 (Claude Code N = 3, Codex N = 2) with the
   pre-registered analysis of section 9 unchanged. With N = 3 the confidence intervals are wider than the
   N = 5 design assumed (section 13, power); the tables show them as they are. Any later run (blocks 3-4,
   more tasks or harnesses) is an update under its own amendment.

**Runs affected:** the rest of the Claude Code main run; the Codex run.

### Amendment 17 (2026-09-30, after the owner stopped the run, before any look at outcomes): stop at N = 2; no Codex main run

**Decision.** The owner, 2026-09-30 about 14:58 UTC: do not start Codex, and stop the Claude
Code run where it is, because the machine had been lagging throughout the run. The stop is about load on the
owner's machine and is blind: no one had looked at main-run outcomes by arm (only counts of trials,
infrastructure failures, plan windows and disk had been reported).

**Change** (replaces amendment 16's volume):
1. The Claude Code runner stopped at 15:02 UTC; the two trials in flight finished and were recorded. Complete
   blocks: 0 and 1, i.e. N = 2 for every arm and task: 15 arms x 15 tasks x 2 = 450 trials.
2. **The primary analysis uses blocks 0-1 only** (450 trials), with the pre-registered analysis of section 9
   unchanged. The 33 valid trials of the incomplete block 2 are not in the primary analysis (block 2 covers
   the arms unevenly); they are reported in an appendix line with their number.
3. **No Codex main run.** The launch reports the Codex pilot (kill test, amendment 8) as a secondary result
   with its actual n. A Codex main run may come later as an update under its own amendment.
4. With N = 2 the confidence intervals are wider than the N = 5 design assumed (section 13, power); the tables
   show them as they are, and the headline stays on cost and verdicts (section 9.2).

**Runs affected:** the main run (stopped); the Codex runs of amendments 15-16 (not run).

### Amendment 18 (2026-09-30, after the analysis, before publication): where the data are released

Section 15 says the raw trajectories are published. They are, in two parts, because the agents' full logs are
large (about 560 MB for the Claude Code run: documents that the tasks give the agent are inside, base64-encoded):
- **Per-trial records in the repository** (`results/main/claude-code/`, `results/pilot/codex/`): each trial's
  Harbor result (tokens, reward, exceptions), the verifier's output and reward, the final-diff and snapshot
  records of amendments 9, 12 and 14, and the approval turns. Layout: `trials/<arm>/<job>/` for the primary
  analysis (blocks 0-1, amendment 17), `appendix-block2/` for the incomplete block, `not-analysed/` for every
  other attempt with its reason.
- **The agents' full logs** (Claude Code's raw stream and the ATIF trajectory per trial; the Codex rollouts) as
  assets of GitHub release v0.1.0, one archive per harness, under the same paths; their sha256 are committed in
  `results/*/*/AGENT_LOGS.json`.
Everything passed `scripts/scrub.py` (keys, the runner's home path, e-mail) before export.

### Amendment 19 (2026-10-06, after the repository was made public, before the launch posts): agent timeouts count as failed trials; the approval-turn mark

**What was wrong.** Sections 5 and 7 say that an agent timeout is a failed trial. The analysis code counted a
trial as passed whenever the verifier returned a reward of 1, and Harbor runs the verifier on the agent's final
state even after a timeout. Two main-run trials were agent timeouts (1,200 s) whose verifier passed afterwards:
placebo-cc-5 on django__django-11265 and planning-with-files on django__django-15957, both in block 1. Both had
been counted as passes. Found on 2026-10-06 while checking the approval-turn records for section 5.1 (neither
trial has one: the timeout ended the run before it was written). No other published trial is affected; the
Codex pilot had no timeouts.

**Change.** `src/skill_placebo/collect.py` counts an agent timeout as a failed trial whatever the reward (with a
test), and the analysis was rerun with nothing else changed (`results/main/claude-code.json`). The effect is on
pass rates only; costs and every R are unchanged:
- planning-with-files vs its placebo: D −17 → −20 pp [−37, −7], Holm-adjusted p 0.178 → 0.043, so its verdict
  changes from "no better than placebo" to **"worse than placebo"**;
- caveman D +3 → +7 pp and agent-skills D −3 → 0 pp (their placebo cc-5 now passes 83%); verdicts unchanged.
The headline becomes "2 of 9 skills beat a same-length placebo, both at Holm-adjusted p = 0.049 (1 worse, 6 no
better)".

**Pilot.** The same rule applies to the Claude Code pilot. One kill-test trial (placebo-cc-5 on django-11265)
and both selection trials of django-13401 were such timeouts. The kill rule uses cost only and does not change;
the caveman placebo's kill-test pass rate becomes 90% (`results/pilot/kill-claude-code.json`,
`results/pilot/SUMMARY.md`). `tasks/selected.json` records django-13401 as 2 of 2 passes, which is 0 of 2 under
this rule; it was not selected either way, so the selected set does not change.

**Section 5.1 mark.** Section 5.1 requires the results table to mark superpowers and every skill whose trials
used the scripted approval turn; the table as first published did not. It now marks superpowers, ponytail and
i-have-adhd, with the counts from the trial records under the table.

**Versions.** Release v0.1.0 (its tag is on commit 29c7426) and the README in PyPI package 0.1.0 show the earlier
numbers; the main branch and the next package version carry the corrected ones.

**Runs affected:** none is rerun; the main-run analysis and the pilot summary are recomputed.
