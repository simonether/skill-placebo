# skill-placebo: pre-registered method

Version 1.0 draft, 2026-09-25. This file is committed to git before any paid run. The commit
history is the timestamp of the pre-registration. After the first paid run the method changes only
through the [Amendments](#15-amendments) section: date, reason, which runs are affected, written
before those runs.

<!-- DRAFT: sections marked TBD are filled from docs/research/ before the pre-registration commit. -->

## 1. Question

Popular agent skills and plugins for coding agents promise better work, fewer tokens, or both.
Most of these promises were never tested against a control that accounts for the simplest
alternative explanation: *any* extra instruction of the same length changes what the agent does and
what it costs.

For each of the 10 most-starred general-purpose coding skills we ask:

1. **Does the skill beat a placebo?** A placebo is a neutral instruction of the same length,
   installed the same way, that adds no new direction.
2. **What does the skill do to cost?** Mean USD per task at list prices, and per solved task.

Secondary questions: skill vs no skill; placebo vs no skill (the size of the placebo effect itself);
the author's README claim vs the measured number, where the README makes a numeric claim.

## 2. Prior art

This project is a replication and extension, not a first. What was already measured:

| Work | Date | What it did | Result |
|---|---|---|---|
| JetBrains AI blog, 3-part series | 2026-07 | caveman, rtk, ponytail on SkillsBench tasks via Harbor, Sonnet 5 | caveman ~8.5% token savings vs 65% claimed, quality flat (p=0.82); rtk +7.6% vs -60..-90% claimed; ponytail -15.4% code vs -54% claimed, cost -10.3% (p=0.004, 251 trials) |
| maxtaylor.me, caveman vs "be brief" | 2026-04 | 24 prompts, 5 arms incl. a "be brief" control (HN 47954745) | "be brief" as an active control |
| SWE-Skills-Bench (arXiv 2603.15401) | 2026-03 | 49 public SWE skills | 39 with zero gain, mean +1.2%, token overhead up to +451% |
| SkillsBench (arXiv 2602.12670) | 2026-02 | curated task-specific skills, 87 tasks | +16.6 pp with curated skills |
| ACES / NVIDIA SkillEvaluator (arXiv 2608.20614) | 2026-08 | paired with/without trials on Harbor, 145 enterprise skills | mean "Skill Lift" 0.21 |
| sjh9714/skill-receipts | 2026-07 | same placebo idea | no published matrix found |
| currenjin/skillbench | 2026-07 | weekly skill benchmark with baseline | abandoned before results |
| Tessl registry "Impact" scores | 2026-02 onward | auto-generated scenarios, with vs without | caveman 0.94x on 2 scenarios |
| `claude plugin eval` (Claude Code 2.1.269) | 2026-09-11 | first-party WITH / W/OUT ablation for one plugin | tool, no public comparison |

TBD: final table with links and exact numbers from `docs/research/2026-09-25-skills-census.md`.

What this project adds: 10 skills in one design; a length-matched placebo arm; two harnesses
(Claude Code and Codex CLI); the method fixed before data; README claims next to measured numbers;
every trajectory published.

## 3. Skills under test

TBD from the census: selection rule, the 10 skills with pinned commit, stars on 2026-09-25, type
(always-on / model-triggered / plugin with hooks), install method as documented by the author,
interactive or not, numeric README claim (quote, file:line), prior measurement. Excluded
candidates are listed with the reason.

## 4. Arms

Every task is run in every arm on every harness with the same model, effort, container image,
tools, permissions, timeout and prompt. Only the installed instruction differs.

| Arm | What is installed |
|---|---|
| **Baseline** | Nothing. Harness defaults. |
| **Placebo** | A neutral instruction of the same length as the skill, installed through the same mechanism. |
| **Skill** | The skill or plugin, installed exactly as its author documents, at the pinned commit. |

### 4.1 Placebo construction

TBD after the census: matching unit (per skill or per length tier), matching tolerance, and the
mechanism mirror for each skill type.

Fixed now:

- The placebo text restates guidance the harness already gives by default (read the task, use the
  available tools, check the work) in neutral wording. It adds length and the presence of an
  instruction, but no new direction on process, verbosity, testing, planning or tool choice.
- It contains no words from the tested skills' names or trigger phrases.
- Length is matched in characters of the text that reaches the model at session start, and token
  counts are reported next to it.
- The placebo corpus is committed in `placebo/` before the first run and never edited afterwards
  except through an amendment.

## 5. Harnesses and models

TBD from `docs/research/2026-09-25-harness-infra.md`: pinned versions of Harbor, Claude Code and
Codex CLI; model IDs; reasoning effort; timeouts; network policy; how each arm is installed.

Fixed now:

- Claude Code and Codex CLI. OpenCode is planned for a later rerun.
- Permissions: the documented non-interactive / auto-approve mode in every arm. Interactive plugins
  run only in a mode their authors document for unattended use; the table marks them.
- One container image per task, identical across arms.

## 6. Tasks

TBD from `docs/research/2026-09-25-task-pool.md`: source datasets and version, candidate pool.

Fixed now:

- 20 tasks with deterministic verifiers in Harbor format. No LLM judges.
- Selection in the pilot: each candidate task runs in the baseline arm on Claude Code; tasks whose
  observed baseline pass rate is between 30% and 70% qualify. If more than 20 qualify, 20 are drawn
  with a fixed seed, stratified by category. The candidate list, seed and pilot results are
  committed before the main run.
- **Pilot runs are not reused as main-run data.** Selecting tasks on baseline results and then
  reusing those results would bias the baseline (regression to the mean). The main run repeats the
  baseline from scratch.
- The same 20 tasks are used on both harnesses. The Codex baseline pass rate is reported as
  observed, even if it falls outside 30-70%.
- Tasks are public and may be in model training data. Contamination affects all arms equally, so
  within-harness comparisons stay valid; absolute pass rates are not claimed to generalise.

## 7. Procedure

- N = 5 trials per task per arm per harness.
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

TBD: pilot size and cost after the per-trial cost is known from the infrastructure research.

Fixed now:

- The pilot (1) selects the 20 tasks (section 6) and (2) runs a kill test: a subset of skills and
  the placebo on a subset of tasks.
- **Kill rule.** If no skill in the kill test shows a non-trivial cost difference vs placebo, the
  project stops at a write-up without a repo release. Non-trivial means a point estimate of R
  outside 0.90-1.10 **and** a 95% CI that excludes 1.

## 12. Budget and stop rules

- API budget: pilot at most $60, whole project at most $300. Any excess is approved by the owner
  before it is spent.
- Before each batch the cost is estimated from the measured cost per trial; spend is recorded in
  `docs/budget.md` after each batch from the trajectories.
- A batch that spends more than 1.5x its estimate is stopped and reviewed.

## 13. Fairness to skill authors

- Each skill is installed the way its author documents, at a pinned commit, including hooks,
  agents and commands when the author ships them.
- Results go to the authors of the tested skills 48 hours before publication. Replies are linked
  from the results page. Installation errors found by authors are fixed and the affected skill's
  arms are rerun in full before publication (an amendment records it).
- Neutral wording. The results say what was measured, on which tasks and models, and nothing about
  intent.

## 14. Reproduction and data release

- One command reproduces a skill's row: `uvx skill-placebo run <owner/repo>` (TBD exact flags).
- Raw trajectories, verifier outputs, token usage and the analysis notebook are published.
- Before release every artifact passes `scripts/scrub.py --check`: no API keys, no local paths,
  no personal e-mail.

## 15. Amendments

None yet.
