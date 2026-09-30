# Results JSON schema (what `scripts/analyze.py` writes, what `scripts/launch/*` reads)

One file per harness and scope: `results/main/claude-code.json`, `results/main/codex.json`. The pilot kill-test
files (`results/pilot/kill-*.json`) carry the `comparisons` part only; the builders compute what is missing.

```jsonc
{
  "harness": "claude-code",
  "meta": {
    "harness": "claude-code", "model": "claude-opus-5-5", "cli_version": "2.1.282",
    "n_trials": 1125,              // valid task trials (last attempt per trial)
    "n_tasks": 15, "n_per_arm": 75, "trials_per_arm": {"baseline": 75, "...": 75},
    "excluded": {"interrupted": 0, "excluded: <reason>": 0},
    "verifier_reruns": 0,          // amendment 9 episodes (their reward counts)
    "pins_seen": [["2.1.282", "claude-opus-5-5"]],   // from session logs (amendment 10)
    "first_trial": "...", "last_trial": "...", "date": "YYYY-MM-DD", "source": "jobs/main/claude-code"
  },
  "comparisons": {                 // skill vs its placebo (METHOD.md 9, 9.1)
    "ponytail": {
      "placebo": "placebo-cc-4",
      "n_tasks": 15, "n_treat": 75, "n_control": 75,
      "cost_treat": 0.16, "cost_control": 0.21,        // mean $ equivalent per trial
      "pass_treat": 1.0, "pass_control": 1.0,
      "ratio": 0.75, "ratio_ci": [0.63, 0.88], "ratio_p": 0.0002,
      "diff_pp": 0.0, "diff_ci_pp": [0.0, 0.0], "diff_p": 1.0,
      "ratio_p_adj": 0.0006, "diff_p_adj": 1.0,         // Holm across skills of this harness
      "verdict": "beats placebo",                       // | trade-off | worse than placebo | no better than placebo
      "cost_per_solved_treat": 0.16, "cost_per_solved_control": 0.21,
      "output_tokens_vs_placebo": {"ratio": 0.63, "ratio_ci": [0.5, 0.8]},
      "mean_output_tokens_skill": 3004, "mean_output_tokens_placebo": 4749
    }
  },
  "vs_baseline": {                 // every skill vs no skill; same statistics (METHOD.md 9)
    "ponytail": {
      "cost_vs_baseline": {"ratio": 0.8, "ratio_ci": [0.7, 0.9], "ratio_p": 0.01},
      "tokens_vs_baseline": {...}, "output_tokens_vs_baseline": {...}, "agent_seconds_vs_baseline": {...},
      "pass_vs_baseline": {"diff_pp": 0, "diff_ci_pp": [0, 0], "diff_p": 1, "pass_arm": 1.0, "pass_baseline": 1.0}
    }
  },
  "placebo_vs_baseline": {"cc-4": {...}}   // same shape, per placebo
}
```

Numbers in this file are illustrative. `results/claims.json` holds the claimed side of the claims table; its
`our_key` values name the fields above (`cost_vs_baseline`, `tokens_vs_baseline`, `agent_seconds_vs_baseline`,
`output_tokens_vs_placebo`, `pass_vs_baseline`; `diff_lines_vs_baseline` is not collected yet).
