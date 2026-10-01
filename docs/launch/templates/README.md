{{scope_banner}}
<p align="center">
{{chart}}
</p>

# skill-placebo

**A placebo-controlled test of the most-starred skills for coding agents: does a skill do better than the same amount of neutral text?**

> Drug trials give the control group a sugar pill. We gave coding agents one: neutral instructions of the same length, installed the same way as each skill.

**{{cc.headline}}.** Control: a same-length neutral placebo, installed like the skill.<br>
{{cc.secondary_line}}<br>
<sub>Measured {{date}} on {{cc.n_tasks}} public tasks (SWE-bench Verified, Terminal-Bench 2.1, OpenThoughts-TBLite) with {{cc.model}} in Claude Code, {{cc.n_per_arm}} trials per arm, {{cc.n_trials}} trials in total. Method registered before the first run: [METHOD.md](METHOD.md). Per-trial records: [`results/`](results/); the agents' full logs: [release v0.1.0](https://github.com/simonether/skill-placebo/releases/tag/v0.1.0) (sha256 in `results/*/*/AGENT_LOGS.json`). Reproduce a row: `{{run_cmd}}`.</sub>

## Results: Claude Code ({{cc.model}})

{{cc.results_table}}

{{cc.ci_note}}

R is the skill's mean cost divided by its placebo's; below 1 the skill is cheaper. D is the pass-rate
difference. Verdicts follow [METHOD.md 9.1](METHOD.md#91-verdict-per-skill-and-harness), with Holm
correction across the {{cc.n_skills}} skills. D stays out of the headline: {{cc.d_sentence}}. This is v1: {{cc.n_per_arm}} trials per arm
([METHOD.md, amendments 16-17](METHOD.md)); more runs come as updates.

## Codex ({{codex.model}}): pilot only, secondary

{{codex.results_table}}

These are the pilot's kill test on Codex: {{codex.n_skills}} skills on {{codex.n_tasks}} tasks, {{codex.n_per_arm}} trials per arm.
The Codex main run did not take place for v1 ([METHOD.md, amendment 17](METHOD.md)); it may come as an update.

## What the READMEs claim, and what we measured

{{claims_table}}

The claims were measured by their authors on other tasks, models and baselines (the "their setup"
column), so a gap between the two columns does not mean the claim was wrong. It shows how much the
number changes in a different setup.

## How it works

- Every skill runs in three arms on the same tasks: no skill, placebo, skill.
- The placebo is neutral text sized to the skill's always-on token footprint (within ±10%, measured),
  delivered through the same mechanism: plugin, hook or memory file ([METHOD.md 4.1](METHOD.md#41-placebo-construction)).
- Cost is recorded tokens times public list prices: an estimate by tokens, not an invoice. The 95% CIs come from a cluster bootstrap over tasks.
- Skills are installed as their authors document, at a pinned commit ([skills.lock.json](skills.lock.json)).
  Every trial is published, including the failed and interrupted ones.

## For skill authors

If your skill was installed wrong or its placebo is unfair to it, [open an issue](https://github.com/simonether/skill-placebo/issues/new?template=skill-install-dispute.yml): skill, commit, what is
wrong, how to check. Every trial is public, so you can point at the exact runs. A confirmed installation error
means your skill's arms are rerun in full, the result is updated, an amendment in METHOD.md records it, and the
issue is linked here ([METHOD.md, amendment 19](METHOD.md)).

## Reproduce

```bash
{{run_cmd_example}}   # one skill: baseline, placebo, skill on the same tasks
```

## Limits

- Two models at medium effort, each harness's default: {{cc.model}} (Claude Code) and {{codex.model}} (Codex). Other models
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
<sub>Made by Simon (@simonether) · I take AI-built apps from demo to production at Keelfast.</sub>
