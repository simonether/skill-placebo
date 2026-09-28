# Skills census: general-purpose coding skills/plugins (2026-09-28)

Date: 2026-09-28. Author: research agent for skill-placebo. Read-only: `gh api` GETs and
raw.githubusercontent.com only; nothing starred, forked, watched or posted.
Legend: **[V]** verified from the named source; **[U]** unverified. `O/R@sha7:path:line` = file:line at that commit.
Written incrementally; sections are appended as each candidate is finished.

## Summary table (filled at the end)

| repo | stars | type | always-on chars | interactive? | Codex support | numeric claim? | prior measurement? |
|---|---|---|---|---|---|---|---|

## Per-candidate sections

### 1. obra/superpowers

- **Meta [V]** (`gh api repos/obra/superpowers`): 292,186 stars; created 2025-10-09; pushed 2026-09-27; MIT;
  `main` HEAD `8ca22dba9a94f28898bbce59f2537ff4d87c747d`; latest release `v6.4.2` (2026-09-25).
- **Components [V]** (`git/trees/8ca22db?recursive=1`): 15 SKILL.md, 170,125 bytes total (largest:
  subagent-driven-development 32,577; writing-skills 26,623; executing-plans 20,405; brainstorming 17,548).
  Hooks: `hooks/hooks.json` = one **SessionStart** hook (matcher `startup|clear|compact`) → `hooks/session-start`.
  No agents/, no commands/. Root `AGENTS.md` (8,983 B) is contributor guidelines, not installed. Manifests:
  `.claude-plugin/plugin.json` yes, `.codex-plugin/plugin.json` yes (`"skills": "./skills/"`, `"hooks": {}`,
  `"capabilities": ["Interactive","Read","Write"]`), plus cursor/devin/kimi/muse manifests.
- **Always-on chars (Claude Code) ≈ 6,021 [V arithmetic, U on exact harness rendering]:**
  15 × (name + description) = 2,615 chars (script over each SKILL.md frontmatter) +
  SessionStart injection = wrapper 226 chars (`hooks/session-start:27`) + full `skills/using-superpowers/SKILL.md`
  3,180 chars (`hooks/session-start:11`) = 3,406. Total 2,615 + 3,406 = **6,021**.
  **Codex:** `.codex-plugin/plugin.json` declares `"hooks": {}`, so no SessionStart injection → ≈ **2,615** [U: depends on
  how Codex renders the skill list]. So the plugin is not the same treatment on both harnesses.
- **Install [V]:** Claude Code `README.md:65` `/plugin install superpowers@claude-plugins-official` (or
  `superpowers-marketplace`, `README.md:75,81`). Codex CLI `README.md:103-119`: `/plugins` → search "superpowers" →
  Install Plugin (official Codex marketplace).
- **Interactive: YES [V].** `skills/brainstorming/SKILL.md:38-56` `<HARD-GATE>`: every path needs the human partner's
  approval ("Present, then stop until you hear yes", `:104`). Brainstorming description (`:3`): "You MUST use this
  before any creative work". **No documented auto-approve / headless user mode found** (code search for
  headless / non-interactive / auto-approve / `claude -p`): `claude -p` appears only in the author's own tests
  (`tests/claude-code/README.md:7`, `tests/claude-code/test-helpers.sh:13`), and `docs/porting-to-a-new-harness.md:613-617`
  warns that non-interactive modes are flaky and says not to depend on them. Per CLAUDE.md, this means exclusion,
  or a documented deviation such as a scripted "yes" turn. A maintainers' decision is needed.
- **Numeric claims:** none in README. There is a qualitative claim: "not uncommon for your agent to work autonomously
  for a couple hours" (`README.md:44`). Evals live in a separate repo, prime-radiant-inc/superpowers-evals (`README.md:385`).
- **Side note [V]:** brainstorming's visual companion loads a logo from the author's site, which works as a
  telemetry ping; opt out with `SUPERPOWERS_DISABLE_TELEMETRY` (`README.md:399`). Set it in runs.
- **Prior measurement:** see "Prior measurements" section below.

### 2. DietrichGebert/ponytail

- **Meta [V]** (`gh api repos/DietrichGebert/ponytail`): 146,937 stars; created 2026-06-12; pushed 2026-09-14; MIT;
  `main` HEAD `e3ba2aa6f1e6f0bc4d69eb09c9f0d0a93af56156`; latest release `v4.10.0` (2026-09-14).
- **Components [V]** (`git/trees/e3ba2aa`): 6 SKILL.md under `skills/` (16,144 B; main `skills/ponytail/SKILL.md`
  6,637 B), plus 6 duplicates in `.openclaw/skills/` and `benchmarks/arms/caveman-SKILL.md` (a benchmark arm, not installed).
  Hooks `hooks/claude-codex-hooks.json` (shared by the Claude and Codex manifests): **SessionStart** (`startup|resume|clear|compact`
  → `ponytail-activate.js`), **SubagentStart** (→ `ponytail-subagent.js`), **UserPromptSubmit** (→ `ponytail-mode-tracker.js`).
  6 commands (`commands/*.toml`, Gemini format). No agents. Rules copies: `.agents/rules`, `.cursor/rules`, `.qoder`,
  `.windsurf`, root `AGENTS.md` (2,593 B, Qoder always-on). Manifests: `.claude-plugin/plugin.json` yes, `.codex-plugin/plugin.json` yes
  (`"hooks": "./hooks/claude-codex-hooks.json"`, `"skills": "./skills/"`).
- **Always-on chars ≈ 7,874 (Claude Code), ≈ 7,874 (Codex) [V arithmetic]:** 6 × (name + description) = 2,645 +
  SessionStart ruleset `getPonytailInstructions('full')` = **5,229** chars (computed by running
  `hooks/ponytail-instructions.js` from the pinned sha against pinned `skills/ponytail/SKILL.md`: header
  `PONYTAIL MODE ACTIVE — level: full` + SKILL.md body without frontmatter and with lite/ultra rows filtered out,
  `hooks/ponytail-instructions.js:77-88`). 2,645 + 5,229 = **7,874**. On top of that, each **subagent** gets another 5,229
  (`hooks/ponytail-subagent.js:25`). UserPromptSubmit injects only on mode-switch commands in Claude/Codex
  (`hooks/ponytail-mode-tracker.js:115-137`, every-prompt injection is Qoder only).
- **Confound [V]:** in Claude Code (not Codex), on the first session where `~/.claude/settings.json` has no `statusLine`, the hook
  appends a "STATUSLINE SETUP NEEDED … Proactively offer to set this up for the user on first interaction" nudge
  (`hooks/ponytail-activate.js:63-106`), about 400 more chars. A fresh container per trial triggers it **every trial**.
  Pre-create `~/.claude/.ponytail-statusline-nudged` or a `statusLine` in the image for all arms.
- **Install [V]:** Claude Code `README.md:133-136` `/plugin marketplace add DietrichGebert/ponytail` then
  `/plugin install ponytail@ponytail`. Codex `README.md:145-149` `codex plugin marketplace add DietrichGebert/ponytail`,
  `codex plugin add ponytail@ponytail`, then "open `/hooks`, review and trust its two lifecycle hooks", which is an interactive
  trust step that must be reproduced headlessly via config [U: how]. Needs `node` on PATH (`README.md:128`).
- **Interactive: NO [V].** Ruleset says "Ship the lazy version and question the complex request in the same response — never stall"
  (fallback copy `hooks/ponytail-instructions.js:62`; same rule in SKILL.md). Only the statusline nudge asks the user something (above).
  Default level `full`; `PONYTAIL_DEFAULT_MODE` env var sets it (`README.md:295`).
- **Numeric claims [V]:** `README.md:33` "~54% less code (up to 94%) · ~20% cheaper · ~27% faster · 100% safe";
  `README.md:34` says this is the mean over 12 feature tasks (Haiku 4.5, n=4). Table at `README.md:85`: LOC -54%, tokens -22%, cost -20%,
  time -27%. Earlier single-shot claim "80-94% less code" was withdrawn as the ceiling rather than the average (`README.md:100`, citing issue #126).
  The author's own benchmark includes a caveman arm (`README.md:86`: caveman tokens +7%, cost +3%).
- **Prior measurement:** see "Prior measurements" section below.

### 3. multica-ai/andrej-karpathy-skills (= forrestchang/andrej-karpathy-skills)

- **Canonical [V]:** `gh api repos/forrestchang/andrej-karpathy-skills` and `repos/multica-ai/andrej-karpathy-skills` return the same
  repo id **1142983825** with `full_name` `multica-ai/andrej-karpathy-skills`. The repo was transferred and the forrestchang URL redirects,
  so there is one repo and no fork question. The README still documents the forrestchang paths (`README.md:105,119`).
- **Meta [V]:** 215,543 stars; created 2026-01-27; pushed 2026-04-20 (inactive since then); **no license file**
  (`license: null`; `.claude-plugin/plugin.json` says `"license": "MIT"`, a contradiction); `main` HEAD
  `2c606141936f1eeef17fa3043a72095b4765b9c2`; no releases.
- **Components [V]:** 1 SKILL.md (`skills/karpathy-guidelines/SKILL.md`, 2,518 B), `CLAUDE.md` 2,357 B (same guidelines),
  `.cursor/rules/karpathy-guidelines.mdc`, `EXAMPLES.md` (not installed). No hooks, agents or commands. `.claude-plugin/plugin.json` yes
  (`"skills": ["./skills/karpathy-guidelines"]`); **no `.codex-plugin`**.
- **Always-on chars [V]:** depends on the install option the author documents.
  (A) plugin: name 19 + description 219 = **238** (skill triggered on demand; body 2,242 chars only when invoked).
  (B) CLAUDE.md: **2,357** always-on (whole file). Option B is the lab-cleanest "always-on rules text" and matches the
  repo's own description ("A single CLAUDE.md file", `README.md:7`).
- **Install [V]:** Claude Code `README.md:105-110` `/plugin marketplace add forrestchang/andrej-karpathy-skills` +
  `/plugin install andrej-karpathy-skills@karpathy-skills`; or `README.md:119` `curl -o CLAUDE.md …/CLAUDE.md`.
  **Codex: not documented** (no "codex"/"AGENTS.md" in README). Putting CLAUDE.md into `AGENTS.md` would be our adaptation and
  must be flagged as such.
- **Interactive: PARTIAL [V].** No approval gate, but the text says "If uncertain, ask." (`CLAUDE.md:12`) and "If something is
  unclear, stop. Name what's confusing. Ask." (`CLAUDE.md:15`). In headless runs this can end a trial with a question.
  Count it as a real effect of the skill, not a harness failure (pre-register this). No non-interactive mode (none needed).
- **Numeric claims:** none. Only qualitative criteria ("fewer unnecessary changes in diffs…", `CLAUDE.md:65`).
- **Prior measurement:** see "Prior measurements" section below.

