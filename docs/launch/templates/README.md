{{scope_banner}}
<p align="center">
{{chart}}
</p>

# skill-placebo

**A placebo-controlled test of the most-starred skills for coding agents: does a skill do better than the same amount of neutral text?**

> Drug trials give the control group a sugar pill. We gave coding agents one: neutral instructions of the same length, installed the same way as each skill.

**{{cc.headline}}.** Control: a same-length neutral placebo, installed like the skill.<br>
<sub>Measured {{date}} on {{cc.n_tasks}} public tasks (SWE-bench Verified, Terminal-Bench 2.1, OpenThoughts-TBLite) with {{cc.model}} in Claude Code, {{cc.n_per_arm}} trials per arm, {{cc.n_trials}} trials in total. Method registered before the first run: [METHOD.md](METHOD.md). Raw trajectories: [`results/`](results/). Reproduce a row: `uvx skill-placebo run <owner/repo>`.</sub>

## Results: Claude Code ({{cc.model}})

{{cc.results_table}}

R is the skill's mean cost divided by its placebo's; below 1 the skill is cheaper. D is the pass-rate
difference. Verdicts follow [METHOD.md 9.1](METHOD.md#91-verdict-per-skill-and-harness), with Holm
correction across the {{cc.n_skills}} skills. D stays out of the headline: with this many tasks its 95% CI
is about ±14 points, too wide to rank skills by.

## Codex ({{codex.model}}, secondary)

{{codex.results_table}}

Codex ran {{codex.n_skills}} skills with {{codex.n_per_arm}} trials per arm, because the owner's ChatGPT Plus
week covers about 100 trials ([METHOD.md, amendment 9](METHOD.md#amendment-9-2026-09-30-after-the-pilot-before-any-main-run-trial-main-run-design-guards-verifier-timeouts-codex)).

## What the READMEs claim, and what we measured

{{claims_table}}

The claims were measured by their authors on other tasks, models and baselines (the "their setup"
column), so a gap between the two columns does not mean the claim was wrong. It shows how much the
number changes in a different setup.

## How it works

- Every skill runs in three arms on the same tasks: no skill, placebo, skill.
- The placebo is neutral text sized to the skill's always-on token footprint (within ±10%, measured),
  delivered through the same mechanism: plugin, hook or memory file ([METHOD.md 4.1](METHOD.md#41-placebo-construction)).
- Cost is recorded tokens times public list prices. The runs used subscriptions, so this is an estimate
  by tokens, not an invoice. The 95% CIs come from a cluster bootstrap over tasks.
- Skills are installed as their authors document, at a pinned commit ([skills.lock.json](skills.lock.json)).
  Every trial is published, including the failed and interrupted ones.

## Reproduce

```bash
uvx skill-placebo run DietrichGebert/ponytail   # one skill: baseline, placebo, skill on the same tasks
```

## Limits

- Two models at their default effort: {{cc.model}} (Claude Code) and {{codex.model}} (Codex). Other models
  can behave differently.
- The tasks are public and probably in the models' training data. That affects every arm equally, but
  absolute pass rates say little about new work.
- Most tasks sat at the ceiling for {{cc.model}}, so the pass rate carries little information here and
  the headline is cost.
- Tasks take minutes. Skills that pay off over long sessions (memory, multi-day plans) are not measured.

## Port me

- [ ] Run a skill on OpenCode or Gemini CLI (`good first issue`)
- [ ] Propose a skill: open an issue with the repository
- [ ] Rerun on fresh tasks (a recent SWE-rebench slice)

## License

MIT, see [LICENSE](LICENSE).

## Badge for tested skills

`[![placebo-tested](https://raw.githubusercontent.com/simonether/skill-placebo/main/docs/badges/<skill>-cc.svg)](https://github.com/simonether/skill-placebo#results-claude-code)`

---
<sub>Made by Simon (@simonether) · I build production-grade AI MVPs at Keelfast.</sub>
