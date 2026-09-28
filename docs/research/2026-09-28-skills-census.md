# Skills census: general-purpose coding skills/plugins (2026-09-28)

Date: 2026-09-28. Author: research agent for skill-placebo. Read-only: `gh api` GETs and
raw.githubusercontent.com only; nothing starred, forked, watched or posted.
Legend: **[V]** verified from the named source; **[U]** unverified. `O/R@sha7:path:line` = file:line at that commit.
Written incrementally; sections are appended as each candidate is finished.

## Summary table

Stars as of 2026-09-28 (`gh api repos/O/R`). Always-on chars = skill/agent/command name+description listing + hook-injected text per
1-prompt session, Claude Code / Codex (arithmetic in each section). CC = Claude Code.

| repo | stars | type | always-on chars (CC / Codex) | interactive? | Codex support | numeric claim? | prior measurement? |
|---|---|---|---|---|---|---|---|
| obra/superpowers | 292,186 | plugin + SessionStart hook + 15 triggered skills | 6,021 / ~2,615 | **YES**: brainstorming HARD-GATE; no documented auto-approve mode | native plugin, but no hook on Codex | no | MindStudio 6-vs-6 (−9% cost, weak); Tessl: brainstorming only |
| mattpocock/skills | 270,705 | triggered (25 skills) | ~4,108 (U: lower) / n.a. | YES when triggered (tdd confirms seams; setup asks) | no native plugin; `npx skills` | no | none found |
| affaan-m/ECC (ex everything-claude-code) | 268,429 | EXCLUDED: collection + memory + harness | not computed | - | - | - | - |
| multica-ai/andrej-karpathy-skills (= forrestchang) | 215,543 | always-on CLAUDE.md, or 1 triggered skill | 2,357 (CLAUDE.md) or 238 (plugin) / not documented | partial ("If uncertain, ask") | not documented (AGENTS.md = our adaptation) | no | Tessl scenario eval "1.14x" only |
| DietrichGebert/ponytail | 146,937 | plugin + SessionStart/SubagentStart hooks | 7,874 / 7,874 (+5,229 per subagent) | no (but a statusline "offer" nudge in CC) | native plugin + hooks (needs `/hooks` trust) | **yes**: −54% LOC, −20% cost, −27% time | JetBrains cost −10.3% p=0.004 (no placebo); Scott Logic: a 7-word prompt beat it |
| JuliusBrussee/caveman | 108,071 | plugin + SessionStart + per-prompt hooks | ~10,190 / ~830 (mode needs `/caveman`) | no (statusline nudge in CC) | skills via `npx skills`; per-session only | **yes**: "cuts 65% of tokens" | JetBrains −8.5% output tokens, p=0.82 quality; maxtaylor: "Be brief." matched it |
| addyosmani/agent-skills | 99,510 | triggered (25 skills + 4 agents + 9 cmds) | 10,915 / 9,266 | partial ("STOP … Wait for resolution") | native plugin | no | LinkedIn head-to-head vs superpowers (U) |
| Leonxlnx/taste-skill | 90,647 | EXCLUDED: frontend/UI design domain | - | - | - | - | - |
| gsd-build/get-shit-done → open-gsd/gsd-core | 64,444 (archived) / 9,899 | EXCLUDED: phase orchestrator | - | - | - | - | - |
| ayghri/i-have-adhd | 51,607 | triggered; opt-in always-on SessionStart | 253 (default) or ~7,237 (always-on, CC only) / 253 | no | native plugin; explicit `$i-have-adhd` only | no | none found |
| OthmanAdi/planning-with-files | 27,153 | triggered, then 6 hooks once a plan file exists | 625 until a plan exists / U | U (no gate seen) | plugin + hooks (docs/codex.md, U) | **yes**: 96.7% (29/30), 3/3 blind A/B, 13.3→5.0 turns | none found |
| EveryInc/compound-engineering-plugin | 25,299 | triggered (36 skills); `/lfg` autonomous | 7,943 / 7,943 | YES by default; documented hands-off `/lfg` (ends in push/PR) | native plugin | no (80/20 philosophy only) | natea/harness-eval (U) |
| nizos/tdd-guard | 2,353 | hooks + separate validation model | not checked | not checked | via successor nizos/probity | not checked | none found |

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

### 4. JuliusBrussee/caveman

- **Meta [V]:** 108,071 stars; created 2026-04-04; pushed 2026-09-27; license `NOASSERTION`. `LICENSE` is MIT with a scope note:
  engine/, proxy/, rewriter/, browse/, mcp/, shrink/ are under BSL-1.1 (`LICENSE:1-5` at sha). The skill/plugin part is MIT.
  `main` HEAD `2fd153c67988e980fb0b2455c90832159a6a5a25`; latest release `v2.7.0` (2026-09-15).
- **Scope warning [V]:** the repo is now a product suite (proxy `caveman claude`, SDKs, MCP, memory, browser). The **skill-only
  track** is what fits our criteria. The proxy is a CLI proxy (excluded, like rtk). The JetBrains test covered the skill only (`README.md:205`).
- **Components [V]** (`git/trees/2fd153c`): 20 SKILL.md under root `skills/` (includes generic workflow skills such as
  `investigate-first`, `lean-build`, `surgical-patch`, `verify-and-stop`, `safe-refactor`, `migration`) + 4 under
  `plugins/caveman/skills/` (Codex plugin). Root `.claude-plugin/plugin.json` has inline hooks: **SessionStart** →
  `src/hooks/caveman-activate.js`, **UserPromptSubmit** → `src/hooks/caveman-mode-tracker.js`. `agents/` has 3 `cavecrew-*.md`
  subagents. `commands/caveman-init.md` + Gemini `.toml`s. `.codex-plugin` only at `plugins/caveman/.codex-plugin/plugin.json`
  (`"skills": "./skills/"`, no hooks). Repo-local `.codex/hooks.json` (echo one-liner) applies only inside this repo.
- **Always-on chars (Claude Code plugin) ≈ 10,190 [V arithmetic; U whether all 20 root skills + 3 agents auto-load from the root plugin]:**
  20 × (name + description) = 3,863 + 3 agents (name + description) = 877 + SessionStart ruleset
  `rulesetBanner('full') + loadFilteredRuleset('full')` = **5,205** (computed by running pinned `src/hooks/caveman-config.js`
  against pinned `skills/caveman/SKILL.md`; `src/hooks/caveman-activate.js:356-362`) + **per-prompt** UserPromptSubmit reinforcement
  **245** chars (`src/hooks/caveman-mode-tracker.js:111-125`, `full`). 3,863 + 877 + 5,205 + 245 = **10,190** per 1-prompt trial.
  Plus a one-time statusline nudge (`src/hooks/caveman-activate.js:405-421`), about 400 chars, which fires in every fresh container.
  Pre-create `~/.claude/.caveman-nudge-shown` in all arms.
  **Codex (author-documented path) ≈ 830 + nothing always-on:** `npx skills add JuliusBrussee/caveman -a codex -g` with
  "Per-session: `/caveman`" (`INSTALL.md:51`). Codex gets the skill descriptions only, and caveman mode must be triggered.
  **The treatment differs materially between harnesses.**
- **Install [V]:** Claude Code `README.md:149` / `INSTALL.md:45` `claude plugin marketplace add JuliusBrussee/caveman && claude plugin install caveman@caveman`.
  Quick start `README.md:101` `npx skills add JuliusBrussee/caveman -g`. Codex `README.md:162` `npx skills add JuliusBrussee/caveman --skill '*' -a codex --yes -g`
  or `INSTALL.md:51`.
- **Interactive: NO [V]** (style rules only; the one "Proactively offer" line is the statusline nudge above). Default level `full`
  (`src/hooks/caveman-activate.js:122`).
- **Numeric claims [V]:** GitHub repo description: "cuts 65% of tokens by talking like a caveman" (`gh api repos/JuliusBrussee/caveman .description`).
  README example "Normal agent · 69 tokens" vs "Caveman agent · 19 tokens" (`README.md:51-52`). Own eval: "50% fewer output tokens at the
  median on top of the terse control" (`README.md:206`, 10 dev questions, length only). Proxy: "-33.2%" input tokens (`README.md:234`; proxy, not skill).
- **Prior measurement [V as cited by the author]:** JetBrains July 2026, skill only, 86 tasks, Claude Code 2.1.200: "8.5% fewer output tokens,
  about 10% cost. No detectable quality change (sign test p = 0.82)" (`README.md:205`,
  https://blog.jetbrains.com/ai/2026/07/speak-to-ai-agents-like-cavemen-tosave-tokens/). The ponytail author's own agentic benchmark
  has a caveman arm (tokens +7%, cost +3%; `DietrichGebert/ponytail@e3ba2aa:README.md:86`). Adobe Research arXiv 2606.24083
  cites the style (`README.md:300`) [U, not opened].

### 5. affaan-m/everything-claude-code (now affaan-m/ECC), EXCLUDE

- **Canonical [V]:** `gh api repos/affaan-m/everything-claude-code` resolves to `affaan-m/ECC` (same id 1136590548), so it was renamed.
- **Meta [V]:** 268,429 stars; created 2026-01-18; pushed 2026-09-28; MIT; `main` HEAD `d3b8a3e908904e242ed2dbe66af62cca71131419`;
  latest release `v2.2.1` (2026-09-08).
- **Components [V]** (`git/trees/d3b8a3e`): 903 SKILL.md (7.87 MB) in total, 292 of them under `skills/`. `.claude-plugin/plugin.json` loads
  `"skills": ["./skills/"]` and `"commands": ["./commands/"]` (94 command .md files); 68 `agents/*.md`. `hooks/hooks.json` (33 KB): PreToolUse ×9,
  PreCompact, SessionStart ×2, PostToolUse ×2, PostToolUseFailure ×2, Stop ×7, SessionEnd. Also has memory persistence (`hooks/memory-persistence/`).
  `.codex-plugin/plugin.json` yes.
- **Why excluded:** it describes itself as an "agent harness operating system" (`README.md:2`) and bundles unrelated domain skills
  (article-writing, brand-voice, bun-runtime…), memory, a security layer and an installer wizard with hook profiles (`README.md:220-248`).
  It is a collection plus memory system plus harness, which the brief excludes. A 3-arm test would measure a whole configuration, not one skill,
  and 292 skill descriptions alone would be tens of thousands of chars of always-on listing [U: not summed].
  Numeric claims: none found in the README grep besides "/test-coverage -> verify 80%+ coverage" (`README.md:737`, a feature, not a claim).

### 6. addyosmani/agent-skills

- **Meta [V]:** 99,510 stars; created 2026-02-15; pushed 2026-09-26; MIT; `main` HEAD `2686b620fc1fed2e8f60c704839c766b8594c6b6`;
  latest release `0.6.11` (2026-09-26).
- **Components [V]** (`git/trees/2686b62`): 25 SKILL.md under `skills/` (344,948 B, the largest bodies in the census: 10-22 KB each).
  9 commands in `.claude/commands/*.md` (Claude manifest `"commands": ["./.claude/commands", "./commands"]`), 4 `agents/*.md`
  (code-reviewer, security-auditor, test-engineer, web-performance-auditor). `hooks/session-start.sh` exists but is
  **not wired by the plugin** (`hooks/session-start.sh:5-8`: "Not wired by the plugin: hosts that already route skills … (Claude Code,
  Codex CLI) would run a second router"). Other hooks (`sdd-cache-*`, `simplify-ignore.sh`) are opt-in. `CLAUDE.md`/`AGENTS.md` at root are
  contributor docs. Manifests: `.claude-plugin/plugin.json` yes, `.codex-plugin/plugin.json` yes (`"capabilities": ["Interactive",…]`).
- **Always-on chars ≈ 10,915 (Claude Code) / ≈ 9,266 (Codex) [V arithmetic; U on agent/command listing]:** 25 × (name + description) = **9,266**
  + 4 agents 819 + 9 commands 830 = 10,915 in Claude Code. Codex plugin ships skills only: 9,266. No hook injection. This is a
  **triggered** skill pack: its effect depends on the model choosing to invoke a skill.
- **Install [V]:** Claude Code `README.md:76-77` `/plugin marketplace add addyosmani/agent-skills` + `/plugin install agent-skills@addy-agent-skills`.
  Codex `README.md:179-183` (Codex CLI v0.122+) `codex plugin marketplace add addyosmani/agent-skills` + `codex plugin add agent-skills@agent-skills`.
  Any agent: `README.md:49` `npx skills add addyosmani/agent-skills`.
- **Interactive: PARTIAL [V].** `skills/using-agent-skills/SKILL.md:66-70` says on unclear specs "**STOP.** Do not proceed with a guess … Wait for
  resolution before continuing". `skills/spec-driven-development/SKILL.md:69` "Ask the human clarifying questions until requirements are concrete".
  `interview-me` asks one question at a time (`README.md:236`). Semi-autonomous mode `/build auto` still needs one plan approval
  (`README.md:38`). **No fully non-interactive mode is documented.** Only triggered skills can gate, so on well-specified Harbor tasks the risk is lower
  than with superpowers [U, pilot must check].
- **Numeric claims:** none about savings. "~95% confidence" (`README.md:236`) is a skill-behaviour target, not a claim.
- **Prior measurement [U, not opened]:** README links a "controlled head-to-head experiment" superpowers vs agent-skills on LinkedIn (`README.md:382`)
  and `docs/comparison.md`. Has an `experimental.evals` block (`.claude-plugin/plugin.json:13-15`).

### 7. Leonxlnx/taste-skill, EXCLUDE (domain: frontend/UI design)

- **Owner [V]:** `gh api search/repositories q="taste-skill in:name"` top hit is `Leonxlnx/taste-skill` (90,647 stars; next is
  senlindesign/taste-skill at 368). Created 2026-02-19; pushed 2026-09-26; MIT; `main` HEAD `ce26fc25c0e5e8cab638f883de62d9a86ee5e45b`.
- **Components [V]:** 13 SKILL.md (302,340 B; `skills/taste-skill/SKILL.md` alone 87,253 B), `.claude-plugin/plugin.json`, no hooks/agents/commands,
  no `.codex-plugin`.
- **Why excluded [V]:** it bills itself as "The Anti-Slop Frontend Framework for AI Agents" (`README.md:8`), with skills for layout, typography,
  motion and image generation (`README.md:63`). This is a design/UI domain skill, which the brief excludes, and it does nothing on a generic Harbor coding task.

### 8. mattpocock/skills (found via addyosmani README comparison; confirmed by stars)

- **Meta [V]:** 270,705 stars (2nd in this census after superpowers); created 2026-02-03; pushed 2026-09-24; MIT;
  `main` HEAD `c55ee46073ed923f86ce59a5eb3b6d895095d1b7`; latest release `v1.2.3` (2026-08-06). Description: "Skills for Real Engineers."
- **Components [V]:** 38 SKILL.md in the repo (163,290 B). The Claude plugin installs **25** of them (explicit list, `.claude-plugin/plugin.json`
  `"skills": [...]`, which leaves out `in-progress/` and `misc/`). No hooks, agents or commands. `CLAUDE.md` (3,737 B) is contributor docs.
  **No `.codex-plugin`**: "A native Codex plugin is on the roadmap" (`README.md:57`).
- **Always-on chars ≈ 4,108 [V arithmetic; U: several skills set `disable-model-invocation` (code search hits: handoff, implement,
  grill-me, wait-what, grill-with-docs), which may drop them from the model's listing and lower the real figure].**
  25 × (name + description) = **4,108**. No hook injection, so this is a **triggered** pack.
- **Install [V]:** Claude Code `README.md:35` `claude plugins install mattpocock-skills` (official marketplace) or `README.md:41`
  `/plugin install mattpocock-skills`. Codex/other `README.md:52` `npx skills@latest add mattpocock/skills` (interactive skill picker;
  "make sure `setup-matt-pocock-skills` is one of them", `README.md:55`). Then `/setup-matt-pocock-skills` once per repo, which **asks** about the issue
  tracker, labels and doc location (`README.md:74-80`). A benchmark has to either skip setup (deviation from the author) or script the answers.
- **Interactive: YES when triggered [V].** `skills/engineering/tdd/SKILL.md:22` "write down the seams under test and confirm them with the user.
  No test is written at an unconfirmed seam". grill-me/grilling are interviews by design. Most descriptions are keyed to user intent
  ("Use when the user wants…"), so on an unattended Harbor task **the likely effect is that nothing triggers** [U, pilot]. No non-interactive mode documented.
- **Numeric claims:** none (README grep for % / Nx found nothing).
- **Prior measurement:** not found [U]. addyosmani `docs/comparison.md` compares against it (not opened).

### 9. ayghri/i-have-adhd (found via topic:claude-skills / topic:claude-code-plugin)

- **Meta [V]:** 51,607 stars; created 2026-05-13; pushed 2026-09-19; MIT; `main` HEAD `839872f9d1cd634fed642b4589ce7226199cc15f`; no releases.
  Description: "A skill to stop your coding agent from burying the answer. ADHD-friendly output."
- **Components [V]:** 1 SKILL.md (`skills/i-have-adhd/SKILL.md`, 7,207 B; `.cursor/` copy). `hooks/hooks.json` = one **SessionStart**
  (→ `hooks/always-on.mjs`) that fires **only if** the opt-in flag `~/.claude/.i-have-adhd-always` exists (`hooks/always-on.sh:9-13`).
  No agents or commands. `.claude-plugin/plugin.json` yes, `.codex-plugin/plugin.json` yes (skills only, no hooks key).
- **Always-on chars [V arithmetic]:** default install = name 11 + description 242 = **253** (triggered).
  Opt-in always-on mode (Claude Code only) = 253 + header ≈197 + SKILL.md body without frontmatter 6,787 ≈ **7,237**
  (`hooks/always-on.sh:36`). Codex: 253 and "Invoke the skill explicitly by typing `$i-have-adhd`. Codex will not activate it automatically"
  (`INSTALL.md:184-185`).
- **Install [V]:** `README.md:30` says to paste a prompt that makes the agent install it from `AGENTS.md`. Explicit: Claude Code `INSTALL.md:122-123`
  `claude plugin marketplace add ayghri/i-have-adhd` + `claude plugin install i-have-adhd@i-have-adhd`; always-on `INSTALL.md:154`
  `touch ~/.claude/.i-have-adhd-always`. Codex `INSTALL.md:180-181` `codex plugin marketplace add ayghri/i-have-adhd --ref main` + `codex plugin add i-have-adhd@i-have-adhd`.
- **Interactive: NO [V].** "A question that comes up mid-work … answer it yourself if you can … If it still needs the reader, surface it once,
  at the end" (`skills/i-have-adhd/SKILL.md:71`).
- **Numeric claims:** none (README grep for % / Nx / tokens found none).
- **Fit:** output-shape skill like caveman (brevity/structure), so it plausibly changes output tokens on any task. For a fair test use the
  documented always-on mode on Claude Code. On Codex it only works if explicitly invoked, so the Codex arm is ~253 chars of listing (expect a null result).
- **Prior measurement:** none found [U].

### 10. get-shit-done (gsd-build/get-shit-done → open-gsd/gsd-core), EXCLUDE (orchestrator / project framework)

- **Canonical [V]:** `gsd-build/get-shit-done` (64,444 stars, created 2025-12-14, MIT) is **archived** (`archived: true`, last push 2026-05-31).
  Its README is only a redirect: "GSD Has Moved … continues as **GSD Core** … https://github.com/open-gsd/gsd-core"
  (`gsd-build/get-shit-done@bdcaab2:README.md:3-9`). Successor `open-gsd/gsd-core`: 9,899 stars; created 2026-05-22; pushed 2026-09-28; MIT;
  default branch `next`, HEAD `9ebd2b006f26f3df9818db1d1924254d346bd4cc`; release `v1.15.0` (2026-09-26).
- **Components [V]:** gsd-core has 72 SKILL.md (171,789 B), 42 hook files (agent-isolation-guard, context-monitor, …) and `.claude-plugin/plugin.json`.
  The archived repo had 67 commands, 37 agents and 15 hooks.
- **Why excluded [V]:** it drives the agent "through a disciplined phase loop" of Discuss → Plan → Execute in "parallel waves" → Verify → Ship,
  per milestone (`open-gsd/gsd-core@9ebd2b0:README.md:28-36`). It starts via `/gsd-new-project` / `/gsd-onboard` (`README.md:49-52`) after an
  interactive installer that "prompts for your runtime" (`README.md:45`). That is a project orchestrator with subagent waves, which the brief excludes, and it
  needs a user-driven command sequence. A single Harbor task prompt would not exercise it as designed. Always-on chars not computed.
  Stars also split between the archived repo and its successor.

### 11. EveryInc/compound-engineering-plugin

- **Meta [V]:** 25,299 stars; created 2025-10-09; pushed 2026-09-28; MIT; `main` HEAD `e80c5c40440b90672d78f032f6dfaedc0daeb292`;
  latest release `compound-engineering-v3.29.0` (2026-09-25).
- **Components [V]:** 36 SKILL.md under `skills/` (43 in the repo incl. test fixtures; 261,774 B total). No plugin hooks (only test fixtures),
  no root `agents/` (reviewer/researcher prompts live inside skills as `references/agents/*.md`). Manifests: `.claude-plugin/plugin.json` yes (default
  `skills/` discovery), `.codex-plugin/plugin.json` yes (`"skills": "./skills/"`, `"capabilities": ["Interactive","Read","Write"]`).
- **Always-on chars [V arithmetic]:** 36 × (name + description) = **7,943**. No hook injection, so this is a **triggered** pack. It mixes coding
  workflow (ce-plan, ce-work, ce-debug, ce-code-review, ce-simplify-code) with non-coding items (ce-product-pulse, ce-strategy, ce-riffrec-feedback-analysis).
- **Install [V]:** Claude Code `README.md:28-29` `/plugin marketplace add EveryInc/compound-engineering-plugin` + `/plugin install compound-engineering`.
  Codex CLI `README.md:83,89` `codex plugin marketplace add EveryInc/compound-engineering-plugin` + `codex plugin add compound-engineering@compound-engineering-plugin`.
- **Interactive: YES by default, with a documented autonomous mode [V].** `skills/ce-brainstorm/SKILL.md:52` Interaction Rules: "one question per turn …
  the blocking-question-tool default". Documented hands-off path: "**Autonomous** -- hand off a feature and let the agent run the whole pipeline"
  `/ce-brainstorm …` then `/lfg` (`README.md:166-170`, `README.md:187`). `lfg` description: "Take a request all the way to done, hands-off … A code change
  ends as an open pull request, pushed without stopping…" (`skills/lfg/SKILL.md` frontmatter). **Caveat:** `/lfg` is user-invoked, which changes the
  prompt in the skill arm only, and it ends in `git push` / PR creation, which fails in an offline Harbor container. Using it needs a pre-registered prompt prefix
  and a matching placebo prefix.
- **Numeric claims:** "80% is in planning and review, 20% is in execution" (`README.md:117`) describes the philosophy, not a measurement.
- **Prior measurement [U]:** `natea/harness-eval` (15 stars, found in the search): "Eval framework that ranks agentic coding frameworks (Superpowers,
  Compound Engineering, Agent S…" (repo description, not opened).

### 12. OthmanAdi/planning-with-files

- **Meta [V]:** 27,153 stars; created 2026-01-03; pushed 2026-09-27; MIT; default branch `master`, HEAD `51c1caa27f9fefe259e45a7cc92fa79ee8787cd7`;
  latest release `v3.21.0` (2026-09-27).
- **Components [V]:** 18 SKILL.md in the repo (302,934 B, mostly per-host mirrors and 5 i18n copies). The Claude plugin registers the canonical
  `skills/planning-with-files/SKILL.md` only (38,148 B; the i18n copies sit one level deeper, `README.md:146`). `hooks/hooks.json`: **SessionStart, UserPromptSubmit,
  PreToolUse, PostToolUse, PreCompact, Stop** (all → `hooks/claude-hook.sh`). SKILL.md frontmatter also declares skill-scoped hooks (disabled when
  running as a plugin). Plugin commands `/plan-goal`, `/plan-loop` (`README.md:290`). `.claude-plugin/plugin.json` yes, `.codex-plugin/plugin.json` yes (+ `.codex/hooks.json`).
- **Always-on chars ≈ 625 until a plan exists [V]:** name 19 + description 606 = **625**. The hooks exit silently when there is no `task_plan.md` / `.planning/`
  (`hooks/claude-hook.sh:99-106`). Once the agent creates a plan, they inject plan context per prompt/tool call (`hooks/claude-hook.sh:155-160`) and a
  PostToolUse nudge after writes, "[planning-with-files] Update progress.md…" (`hooks/claude-hook.sh:250`, 124 chars). So this is **triggered, then self-reinforcing**.
- **Install [V]:** Claude Code `README.md:397-398` `/plugin marketplace add OthmanAdi/planning-with-files` + `/plugin install planning-with-files@planning-with-files`.
  Quick install for any agent `README.md:55` `npx skills add OthmanAdi/planning-with-files --skill planning-with-files -g`. Codex: `README.md:161` → `docs/codex.md`
  ("Skills + Hooks") [U: not opened].
- **Interactive:** no approval gate found in the parts read [U: 38 KB SKILL.md not fully read]. "Optional gated mode can request continuation"
  (`.claude-plugin/plugin.json` description).
- **Borderline scope:** part of the value is session recovery across `/clear`/crash, which works like a memory system, and "explicit catchup modes may read
  same-project local session records" (plugin.json). The planning-discipline part fits our criteria; the recovery part is irrelevant to single-session Harbor tasks.
- **Numeric claims [V]:** badge "benchmark-96.7%_pass_(29/30)" and "blind_A/B-3/3_wins" (`README.md:33-34`); "turned a 13.3-turn re-orientation into 5.0
  turns" (`README.md:75`). The author caveats that 96.7% "measures file-pattern fidelity … not goal-drift" (`README.md:702`); chart alt text: "assertions passed
  29 of 30 vs 2 of 30 … average rubric score 10.0 vs 6.8" (`README.md:707`).
- **Prior measurement:** none independent found [U].

### Also screened and excluded (from the 7 `gh api search/repositories` queries, sort=stars, 2026-09-28)

One line each; stars from the search output.
- shanraisshan/claude-code-best-practice (66,462): a guide/reference repo; no plugin manifest (tree has 0 `plugin.json`); ships sound-effect hooks. Guide, not a skill.
- anthropics/skills (178,667): collection of domain skills (office docs etc.). Collection.
- thedotmack/claude-mem (94,802), NevaMind-AI/memU, zilliztech/memsearch, rohitg00/pro-workflow: memory systems.
- rtk-ai/rtk (81,838), headroomlabs-ai/headroom (73,962): CLI/tool-output proxies.
- Graphify-Labs/graphify (121,882), Egonex-AI/Understand-Anything (84,346), DeusData/codebase-memory-mcp: knowledge graph / MCP.
- nextlevelbuilder/ui-ux-pro-max-skill (131,033), Leonxlnx/taste-skill, cathrynlavery/diagram-design, tt-a1i/archify, nexu-io/open-design: design/diagram domain.
- code-yeongyu/oh-my-openagent (69,602), ruvnet/ruflo, stablyai/orca, NousResearch/hermes-agent: orchestrators / agents.
- wshobson/agents (40,038), alirezarezvani/claude-skills, VoltAgent/awesome-*, ComposioHQ/awesome-claude-skills, hesreallyhim/awesome-claude-code, sickn33/agentic-awesome-skills: marketplaces / awesome-lists.
- blader/humanizer (52,360), mvanhorn/last30days-skill, K-Dense-AI/scientific-agent-skills, cloudflare/security-audit-skill: prose / research / science / security domain.
- Low-star general coding workflow plugins below the bar: ramziddin/solid-skills (600), tzachbon/smart-ralph (550), athola/claude-night-market (339), kunchenguid/kun (365).

## Prior measurements (independent or semi-independent)

Numbers below are as reported by each source. Pages were read via WebFetch summaries, so re-check any number before quoting it publicly.
- **JetBrains, caveman (July 2026)** https://blog.jetbrains.com/ai/2026/07/speak-to-ai-agents-like-cavemen-tosave-tokens/ (Denis Shiryaev): Harbor 0.17,
  Claude Sonnet 5 at low effort, 86/87 SkillsBench tasks, ~240 billed trials, ~USD 106. Output tokens **−8.5%** (advertised −65%), cost about −10%,
  quality sign test **p = 0.82**. Skill **forced on** ("this is the ceiling"). Also quoted by the caveman author (`JuliusBrussee/caveman@2fd153c:README.md:205`).
- **JetBrains, ponytail (July 2026)** https://blog.jetbrains.com/ai/2026/07/ponytail-skill-claude-tested/: Harbor 0.18, Claude Code 2.1.201 headless,
  claude-sonnet-5 at medium effort, 80 paired tasks. Code **−15.4% (p = 0.088)**, cost **−10.3% (p = 0.004)**, time −11%, quality no significant difference.
  Installed normally, the skill "self-activated **zero times**" in ten sessions, so they forced the ruleset via a SessionStart hook. **No placebo arm.**
- **JetBrains, rtk (July 2026)** https://blog.jetbrains.com/ai/2026/07/rtk-claude-code-token-savings/: same setup, 425 billed trials. Cost **+7.6% at low effort
  (p = 0.004)**, +0.1% at high (p = 0.99), turns +13.8% (p = 0.03), quality tied. rtk is out of scope (CLI proxy); listed only as method context.
- **Scott Logic, ponytail (2026-06-16)** https://blog.scottlogic.com/2026/06/16/ponytail-yagni-and-the-problem-with-prompt-benchmarks.html (Colin Eberhardt):
  promptfoo single-shot on Claude Haiku. Mean LOC: baseline 108, "YAGNI principles" 10.4, ponytail 8.25, "Follow YAGNI principles, and one-liner solutions" **6.9**.
  A seven-word prompt beat the skill on the skill's own benchmark; correctness 100% everywhere. This is the closest thing to a **placebo/active-control result** that exists.
  The ponytail author later rebuilt the benchmark (`README.md:100`, issue #126) and reports his own "YAGNI + one-liners" arm (`README.md:87`).
- **maxtaylor.me, caveman vs "Be brief." (2026-04-29)** https://www.maxtaylor.me/articles/i-benchmarked-caveman-against-two-words (HN item 47954745,
  "I benchmarked Claude Code's caveman plugin against 'be brief.'", 89 points, per the HN API): Opus 4.7, 24 prompts. Mean tokens: baseline 636, "Be brief." 419,
  caveman lite 401 / full 404 / ultra 449; quality 0.985 / 0.985 / 0.976 / 0.975 / 0.970. **"Be brief." matched caveman.** Chat prompts, not agentic tasks.
- **MindStudio, superpowers** https://www.mindstudio.ai/blog/5-claude-code-skills-cut-token-costs-70-percent-benchmarked: "Twelve automated sessions. Six with
  Superpowers, six without". Reports −9% cost, −14% tokens. n = 6 per arm, vendor blog, no CI. Weak evidence.
- **Tessl registry**: karpathy-guidelines Quality 83%, Impact 92% "1.14x", "Average score across 3 eval scenarios"
  (https://tessl.io/registry/skills/github/multica-ai/andrej-karpathy-skills/karpathy-guidelines/quality). superpowers: only `brainstorming` has evals,
  Impact 100% "1.81x"; the other 14 skills show "No eval scenarios have been run" (https://tessl.io/registry/skills/github/obra/superpowers). These are registry scenario evals,
  not cost/pass-rate on real tasks.
- **SWE-Skills-Bench (arXiv 2603.15401)** https://arxiv.org/abs/2603.15401: 49 public SWE skills, ~565 task instances, paired with/without. "39 of 49 skills
  yield zero pass-rate improvement", average +1.2%, 3 skills degrade (up to −10%) (per search-result abstract). Whether any census skill is among the 49 was not checked [U].
- **Also seen, not opened [U]:** arXiv 2608.11888 "Agent Skills Can Be Harmful…"; InfoQ 2026-08 on the ponytail benchmark correction; addyosmani's linked LinkedIn
  "superpowers vs agent-skills" experiment (`README.md:382`); natea/harness-eval (ranks Superpowers, Compound Engineering…); Adobe arXiv 2606.24083 (caveman style).
- **Never measured independently (as far as found):** addyosmani/agent-skills, mattpocock/skills, i-have-adhd, compound-engineering, planning-with-files.
  karpathy-skills has only Tessl scenario evals, and superpowers only a 6-vs-6 vendor blog.

### 13. nizos/tdd-guard (reserve, only partly checked)

- **Meta [V]:** 2,353 stars; created 2025-07-07; pushed 2026-09-14; MIT; `main` HEAD `2579ec1823fac5f4afb73be678d9c500b19885ac`; release `v1.7.0` (2026-06-23).
- Hook-based TDD enforcement for Claude Code. Install `README.md:43-44` `/plugin marketplace add nizos/tdd-guard` + `/plugin install tdd-guard@tdd-guard`.
  The README says it "grew into [Probity]" (nizos/probity, 215 stars; adds Codex) and "New projects should start there" (`README.md:10-13`).
  It validates edits with a separate model ("Choose faster or more capable models", `README.md:29`), which adds its own API spend outside the agent trajectory
  and complicates cost accounting. Always-on chars, interactivity and claims were **not checked**.

