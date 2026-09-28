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

