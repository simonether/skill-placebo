# Harness infrastructure research: Harbor + Claude Code + Codex (OpenCode deferred)

Date: 2026-09-25. Author: research agent for skill-placebo.
Scope: how to run a 3-arm experiment (no skill / length-matched placebo / real skill or plugin) on
Harbor tasks with deterministic verifiers, using Claude Code (Anthropic API key) and Codex CLI
(OpenAI API key). OpenCode on an open-weight model is deferred to a later rerun (section C/D kept short).

Legend: **[V]** verified from source code, CLI output or official docs. **[U]** unverified or inferred;
it needs a check in the pilot. "harbor@v0.23.0:path:line" means file:line in
https://github.com/harbor-framework/harbor at tag v0.23.0 (commit 3c305dc). I read it from a local
clone at that tag. `main` (31668af, 2026-09-24) differs from v0.23.0 in places, and those
differences are noted where they matter.

No paid API calls were made. Harbor 0.23.0 was installed into an isolated scratch venv only to read its help output and source.

---

## A. Harbor

### A.1 Version, provenance, install
- Latest stable on PyPI: **harbor 0.23.0**, uploaded 2026-09-12T04:55:10Z. Nightly `0.23.1.devYYYYMMDD` builds come out daily (latest 0.23.1.dev202609240431). Source: `https://pypi.org/pypi/harbor/json`. [V]
- Provenance: GitHub release `v0.23.0` of harbor-framework/harbor was published at 2026-09-12T04:55:17Z, 7 s after the PyPI upload. The PyPI README links harborframework.com and harbor-framework/harbor-cookbook. `diff -r` of the installed wheel against the repo tag `src/harbor` shows only build artifacts (viewer static, leaderboard, debug_checker). [V]
- Requires Python >= 3.12 (PyPI `requires_python`). [V]
- Install: `uv tool install harbor==0.23.0` (or `uvx --from harbor==0.23.0 harbor ...`). Pin the version, because the CLI changes weekly: v0.23.0 → main already touches claude_code.py (+86 lines), codex.py (+207) and the jobs CLI. [V]

### A.2 `harbor run` flags that matter (from `harbor run --help`, v0.23.0) [V]
| Need | Flag |
|---|---|
| Agent | `-a/--agent claude-code \| codex \| opencode \| ...` or `module.path:ClassName` (custom) or `acp:<agent>` |
| Model | `-m/--model anthropic/claude-sonnet-5`, `openai/<model>`, `openrouter/<vendor>/<model>` (repeatable) |
| Agent kwargs | `--ak key=value` (value parsed as JSON, then Python literal, then string: harbor@v0.23.0:src/harbor/cli/utils.py:111-141). Schema: `harbor agent schema <agent>` |
| Agent env | `--ae KEY=VALUE`. Overlaid on agent **setup and run** exec only, not on the verifier (harbor@v0.23.0:src/harbor/trial/trial.py:1572, environments/base.py:443-456) |
| Skills | `--skill <local dir \| org/repo[@ref] \| https://github.com/o/r/tree/<ref>/<subdir>>` (repeatable) |
| Attempts per task | `-k/--n-attempts` (default 1) |
| Concurrency | `-n/--n-concurrent` (default 4); `--n-concurrent-agents` caps concurrent agent phases |
| Retries | `-r/--max-retries`, `--retry-include/--retry-exclude <ExceptionType>` |
| Timeouts | `--timeout-multiplier`, `--agent-timeout-multiplier`, `--verifier-timeout-multiplier`, `--agent-setup-timeout-multiplier`, `--environment-build-timeout-multiplier` |
| Dataset/tasks | `-d name@version`, `-p <local task or dataset dir>`, `-t org/name` (single registry task), `-i/--include-task-name <glob>`, `-x/--exclude-task-name <glob>`, `-l/--n-tasks N`, `--repo`, `--registry-path` |
| Prompt add-on | `--extra-instruction-path <file>` / `--extra-instruction <text>`. These append to the task instruction (user prompt) |
| Environment | `-e/--env docker` (default) \| `daytona` \| `modal` \| `apple-container` \| ...; `--mounts '<json>'` (Docker Compose volume format), `--override-cpus/--override-memory-mb`, `--force-build`, `--no-delete` |
| Output | `-o/--jobs-dir` (default `jobs`), `--job-name` (default timestamp), `--artifact <container path>` |
| Misc | `-y/--yes`, `--env-file`, `--debug`, `--install-only`, `--dry-run`, `-c/--config job.yaml` (repeatable), `--print-config` |

Registry datasets relevant here (from repo `registry.json`): `terminal-bench@2.0` (89 tasks), `terminal-bench-sample@2.0` (10 tasks, good for the pilot), `swebench-verified@1.0` (500), `terminal-bench-pro@1.0` (200). [V]

### A.3 Agent names and kwargs (`harbor agent schema <name>`) [V]
- **claude-code** (harbor@v0.23.0:src/harbor/agents/installed/claude_code.py:50-96): `version`, `prompt_template_path`, `config` (native settings.json, as a path or inline JSON), `max_turns`, `reasoning_effort` (`low|medium|high|xhigh|max` → `--effort`), `thinking_display`, `max_budget_usd` (→ `--max-budget-usd`), `fallback_model`, `append_system_prompt` (→ `--append-system-prompt`), `allowed_tools`, `disallowed_tools`, `permission_mode` (default `bypassPermissions`), `max_thinking_tokens` (→ env `MAX_THINKING_TOKENS`), `memory_dir`. On `main` it also has `disable_web_search`.
- **codex** (codex.py:38-58): `version`, `prompt_template_path`, `config` (native config.toml, path or inline JSON), `reasoning_effort` (`none|minimal|low|medium|high|xhigh|max` → `-c model_reasoning_effort=`), `reasoning_summary`, `web_search`. On `main` it also has `disable_web_search`.
- **opencode** (opencode.py:38-44): `version`, `prompt_template_path`, `config` (rejected at runtime: opencode lacks the `native_config` capability), `variant` (→ `--variant`), `opencode_config` (dict deep-merged into `~/.config/opencode/opencode.json`).
- The kwargs models use `extra="forbid"` (harbor@v0.23.0:src/harbor/agents/options.py:52-55). **There is no generic "extra CLI flags" kwarg.** Every value is shell-quoted into one known flag, so you cannot smuggle in `--plugin-dir` or `--dangerously-bypass-hook-trust`. To add flags you need an env var or a custom agent subclass (A.8).
- Several claude-code options read **host** env vars as fallbacks: `CLAUDE_CODE_MAX_TURNS`, `CLAUDE_CODE_EFFORT_LEVEL`, `MAX_THINKING_TOKENS` (claude_code.py:51-92). So do `CLAUDE_CODE_DISABLE_ADAPTIVE_THINKING` and `CLAUDE_CODE_MAX_OUTPUT_TOKENS` (claude_code.py:1805, 1824). Run Harbor from a clean shell.

### A.4 How Claude Code is run inside the container [V]
- Install (claude_code.py:425-450): if `claude` is missing, or its version differs from `--ak version`, Harbor installs `curl bash nodejs npm procps`. It then runs `curl -fsSL https://downloads.claude.ai/claude-code-releases/bootstrap.sh | bash -s -- <version>`. Alpine uses npm instead.
- Env set by `run()` (claude_code.py:1801-1836): `ANTHROPIC_API_KEY` (or `ANTHROPIC_AUTH_TOKEN`), `ANTHROPIC_MODEL=<model without provider prefix>`, `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1`, `IS_SANDBOX=1` (so bypassPermissions works as root), `FORCE_AUTO_BACKGROUND_TASKS=1`, `ENABLE_BACKGROUND_TASKS=1`, and **`CLAUDE_CONFIG_DIR=/logs/agent/sessions`**. Anything installed into `~/.claude` in the image is therefore invisible, except `~/.claude/skills`, which gets copied (claude_code.py:1838-1845).
- If `ANTHROPIC_BASE_URL` is set, Harbor forwards it and also pins `ANTHROPIC_DEFAULT_{SONNET,OPUS,HAIKU}_MODEL` and `CLAUDE_CODE_SUBAGENT_MODEL` to the main model (claude_code.py:1817-1821). **Gotcha [V]:** this research shell runs inside Claude Code and has `ANTHROPIC_BASE_URL` set. Launching harbor from such a shell would forward that URL into every container. Use `env -u ANTHROPIC_BASE_URL -u CLAUDE_CODE_OAUTH_TOKEN harbor run ...` or a plain terminal.
- Auth: the API key is used by default. `CLAUDE_CODE_OAUTH_TOKEN` is forwarded too, and is used only if `CLAUDE_FORCE_OAUTH=1` or no API key is present (claude_code.py:1709-1790). Harbor docs `core-concepts/jobs/environment-variables.mdx:97-112` list the auto-forwarded credentials. To guarantee API-key billing, unset `CLAUDE_CODE_OAUTH_TOKEN` on the host.
- Command (claude_code.py:1886-1901): `printf "%s" "$INSTR" | claude --verbose --output-format=stream-json [--settings /tmp/claude-code-settings/settings.json] <flags from kwargs> --print 2>&1 | tee /logs/agent/claude-code.txt`. `--permission-mode=bypassPermissions` is among the default flags.
- Model/effort: `-m anthropic/claude-sonnet-5` → `ANTHROPIC_MODEL=claude-sonnet-5`. `--ak reasoning_effort=medium` → `--effort medium`. Note: per Claude Code docs the env var `CLAUDE_CODE_EFFORT_LEVEL` overrides `--effort` (https://code.claude.com/docs/en/env-vars.md, lines 111, 270). Do not also set it via `--ae`.

### A.5 `--skill`: what it does and does not do [V]
- Resolution (harbor@v0.23.0:src/harbor/skills.py): `org/repo[@ref]` means github.com, **subdir `skills/`**. The ref is resolved to a SHA with `git ls-remote`, and the repo is sparse-checked-out into `~/.cache/harbor/skills/<host>/<org>/<name>/<sha>/`. A path must be a dir containing `SKILL.md`, or a root whose **every** non-hidden child dir contains `SKILL.md`. Otherwise it raises `ValueError` (skills.py:393-428). Provenance (name, digest, git_url, commit) goes into the job lock file (docs `core-concepts/jobs/skills.mdx`).
- Upload: each skill goes to `/harbor/skills/<name>` in the sandbox, after the healthcheck and before agent setup (trial.py:1476-1537).
- Registration per agent:
  - claude-code: `cp -r /harbor/skills/* $CLAUDE_CONFIG_DIR/skills/`, i.e. `/logs/agent/sessions/skills` (claude_code.py:1627-1639)
  - codex: `$HOME/.agents/skills/` (codex.py:1197-1205)
  - opencode: `~/.config/opencode/skills/` (opencode.py:447-455)
- **Only SKILL.md skill directories are handled.** Plugin **hooks, agents, commands, MCP servers and `.claude-plugin/plugin.json` are ignored.** For obra/superpowers the SessionStart hook (`hooks/hooks.json` → `hooks/session-start`) is what injects the `using-superpowers` bootstrap text. With `--skill obra/superpowers`, Claude only sees 14 skill descriptions and never gets the bootstrap. That is a different treatment from "superpowers installed".
- Repo compatibility checked via `gh api`:
  - `obra/superpowers@v6.4.1`: `skills/` holds 14 dirs, each with SKILL.md. OK.
  - `DietrichGebert/ponytail`: 6 skill dirs. Probably OK [U].
  - `JuliusBrussee/caveman`: `skills/` contains `generated/` and `native/` without SKILL.md, so **`--skill JuliusBrussee/caveman` will raise**. Use `https://github.com/JuliusBrussee/caveman/tree/<ref>/skills/caveman` per skill.

### A.6 Placebo arm: injecting custom instructions / skills from a local path
| Route | Claude Code | Codex | Notes |
|---|---|---|---|
| Local skill dir | `--skill ./arms/placebo/skills` [V] | same [V] | Same mechanism as the "skills-only" real arm, so best matched to `--skill org/repo` |
| System-prompt text | `--ak append_system_prompt="$(cat placebo.md)"` → `--append-system-prompt` [V] | `--ak config='{"developer_instructions":"..."}'`. `developer_instructions` is a documented config.toml key (https://learn.chatgpt.com/docs/config-file/config-reference) [V] | Different position from CLAUDE.md/AGENTS.md |
| SessionStart hook text (matches how superpowers/caveman/ponytail inject) | `--ak config=arms/placebo/settings.json` holding `{"hooks":{"SessionStart":[{"hooks":[{"type":"command","command":"cat /opt/placebo/ctx.md"}]}]}}`. Harbor passes it as `--settings` (claude_code.py:1865-1901). The file reaches the container via `--mounts`. `-p` sessions treat the folder as trusted, so settings hooks run (https://code.claude.com/docs/en/hooks.md "Workspace trust") [V docs; U end-to-end] | Needs hook trust (A.8) | Best-matched placebo for hook-based plugins |
| Sham plugin (same file layout and token counts as the real plugin) | mount + `--ae CLAUDE_CODE_PLUGIN_DIRS=/opt/plugins/sham` (A.7) | custom agent (A.8) | **Recommended placebo for the full-plugin arm** |
| CLAUDE.md / AGENTS.md file | No native kwarg. `memory_dir` goes to auto-memory (`$CLAUDE_CONFIG_DIR/projects/-app/memory`), not CLAUDE.md (claude_code.py:1641-1654). You need a subclass to write `$CLAUDE_CONFIG_DIR/CLAUDE.md` | Codex reads `$CODEX_HOME/AGENTS.md` (global scope; https://learn.chatgpt.com/docs/agent-configuration/agents-md). Harbor's CODEX_HOME is `/tmp/codex-home` (codex.py:81), so this also needs a subclass | Do **not** drop files into the task workdir (`/app`). Some verifiers check repo state (e.g. fix-git) |
| Prompt append | `--extra-instruction-path file` | same | Changes the user turn. Only good as a "prompt-level" control |

Length matching: `claude plugin details <plugin>` prints "Projected token cost: Always-on ~N tok … on-invoke" per skill/agent/command. Hooks get no estimate (https://code.claude.com/docs/en/plugins/measure.md lines 24-62). Use it with a tokenizer count of the hook output to match the sham plugin to the real one.

### A.7 Real-skill arm with a full Claude Code plugin (hooks + agents + commands) [V docs, U end-to-end]
The cleanest route needs **no Harbor code**:
- Claude Code ≥ 2.1.280 supports `CLAUDE_CODE_PLUGIN_DIRS`. It lists plugin directories to load for the session, each loaded the way `--plugin-dir` loads one: absolute paths, `:`-separated. Source: https://code.claude.com/docs/en/env-vars.md line 334. Local CLI 2.1.280 `--help` also shows `--plugin-dir` and `--plugin-url`.
- Plugins loaded this way are "session-only" (`<name>@inline`), with hooks, skills, agents and commands (https://code.claude.com/docs/en/plugins/loading.md line 52; cli-reference.md line 771).
- Steps:
  1. Vendor the plugin at a pinned tag on the host: `git clone --depth 1 --branch v6.4.1 https://github.com/obra/superpowers vendor/superpowers`.
  2. Bind-mount it: `--mounts '[{"type":"bind","source":"/abs/vendor/superpowers","target":"/opt/plugins/superpowers","read_only":true}]'`. The format is `ServiceVolumeConfig` (harbor@v0.23.0:src/harbor/models/trial/config.py:45-52), Docker only.
  3. Add `--ae CLAUDE_CODE_PLUGIN_DIRS=/opt/plugins/superpowers`.
  4. Pin `--ak version=2.1.282` (npm latest on 2026-09-24), because Harbor installs "latest" otherwise.
- Hooks in `-p` mode: Claude Code "treats the folder as trusted", so hooks run (hooks.md, Workspace trust). Plugin hooks use `${CLAUDE_PLUGIN_ROOT}`. superpowers' hook needs `bash`, while caveman and ponytail need `node`. Harbor installs nodejs/npm for claude-code (claude_code.py:432-434), so node is present.
- Alternatives, if mounts are not available (Daytona/Modal) or you want the "installed from marketplace" path:
  - (a) A subclass whose `setup()` calls `environment.upload_dir(local_plugin, "/opt/plugins/x")`.
  - (b) A subclass that appends `claude plugin marketplace add /opt/plugins/x && claude plugin install x@<marketplace>` to the setup command. It must run with `CLAUDE_CONFIG_DIR` already set. Overriding `_build_register_skills_command` does that, because its output is appended to the setup command executed with the run env (claude_code.py:1838-1863).
  - (c) `CLAUDE_CODE_PLUGIN_SEED_DIR`, a pre-populated plugins dir baked into an image (env-vars.md line 338).
  - `extraKnownMarketplaces`/`enabledPlugins` in `--settings` is **not** reliable. A plugin enabled only in settings "isn't fetched onto a machine where it isn't installed" unless the source is relative-path or seeded (plugins/loading.md line 145).
- Verification in the pilot: look for the hook's injected text or `Skill` tool calls in `/logs/agent/sessions/projects/-app/*.jsonl`. `claude --plugin-dir X plugin list` inside the container should show `X@inline`.

### A.8 Codex specifics (Harbor side) [V unless marked]
- Agent `codex`. Install: `npm install -g @openai/codex[@version]`, using nvm Node 22 if node is missing (codex.py:343-370).
- `CODEX_HOME=/tmp/codex-home` (codex.py:81, 1352-1360). Harbor uploads the effective `config.toml` there (user `--ak config` merged with runtime inputs), then runs setup (auth symlink + skills copy).
- Auth: **`OPENAI_API_KEY` by default**. Harbor writes `$CODEX_HOME/auth.json` as `{"OPENAI_API_KEY": ...}`. ChatGPT-login `auth.json` is used only if `CODEX_AUTH_JSON_PATH=<file>` or `CODEX_FORCE_AUTH_JSON=1` (codex.py:1299-1330, 1344-1395).
- Command (codex.py:1432-1447): `codex exec --dangerously-bypass-approvals-and-sandbox --skip-git-repo-check --model <model> --json --enable unified_exec [-c model_reasoning_effort=...] -- '<instruction>' | tee /logs/agent/codex.txt`. Sessions are copied to `/logs/agent/sessions`.
- Model: `-m openai/<model>`. Harbor strips the prefix (codex.py:1338). Effort: `--ak reasoning_effort=low|medium|high|...`.
- Skills (`--skill`) are copied to `$HOME/.agents/skills` (codex.py:1197-1205). That is Codex's documented user-level skills dir. Codex also scans `$CWD/.agents/skills` up to the repo root, `/etc/codex/skills`, and **bundled system skills**, which are present in every arm. The skills catalog budget is at most 2% of the context window, or 8,000 chars (https://learn.chatgpt.com/docs/build-skills).
- AGENTS.md: global scope is `$CODEX_HOME/AGENTS.override.md` or `AGENTS.md`. Project scope walks root→cwd, capped at `project_doc_max_bytes` = 32 KiB (https://learn.chatgpt.com/docs/agent-configuration/agents-md). The native placebo route is `developer_instructions` via `--ak config`. An AGENTS.md needs a subclass.
- **Plugins in Codex 0.156.1 (local `codex plugin --help`):**
  - Commands are `codex plugin marketplace add <path|owner/repo[@ref]|url> [--ref] [--sparse]` and `codex plugin add PLUGIN@MARKETPLACE`. There is **no** `install` subcommand.
  - Features `plugins`, `hooks` and `remote_plugin` are stable and on (`codex features list`).
  - **Claude-format compatibility** [V source on openai/codex main]: marketplace discovery includes `.agents/plugins/marketplace.json`, `.claude-plugin/marketplace.json` and `.cursor-plugin/marketplace.json` (codex-rs/core-plugins/src/marketplace.rs:21-24). Manifests can be `.codex-plugin/plugin.json` or `.claude-plugin/plugin.json` (codex-rs/utils/plugins/src/plugin_namespace.rs:134; core-plugins/src/manifest.rs:698).
  - Codex sets `CLAUDE_PLUGIN_ROOT`/`CLAUDE_PLUGIN_DATA` for plugin hooks, for compatibility (https://learn.chatgpt.com/docs/hooks).
  - Not verified: whether Claude `commands/` and `agents/` are honored. The manifest parser reads `commands` (manifest.rs:75, 212) [U for agents].
- **Hooks need trust in Codex.** "Installing or enabling a plugin doesn't automatically trust its hooks; Codex skips plugin-bundled hooks until you review and trust" (learn.chatgpt.com/docs/hooks).
  - Trust is stored as `[hooks.state."<key>"] trusted_hash = "<hash>"` in user config.toml (codex-rs/config/src/hook_config.rs:32; core/tests/common/hooks.rs:55-63).
  - `codex exec --dangerously-bypass-hook-trust` runs them without trust (local `codex exec --help`).
  - **Harbor does not pass that flag.** Hook-bearing plugins under Codex therefore need a subclass that appends it (sketch in the Recommended pipeline section).
- What the plugins actually ship for Codex [V via gh api]:
  - superpowers `.codex-plugin/plugin.json` has `"skills": "./skills/", "hooks": {}`, i.e. **no hooks for Codex**. Its `.agents/plugins/marketplace.json` names the marketplace `superpowers-dev`.
  - ponytail's `.codex-plugin/plugin.json` points hooks at `./hooks/claude-codex-hooks.json`, so it does have hooks.
  - caveman has no `.codex-plugin`. Its `.claude-plugin/plugin.json` declares SessionStart and UserPromptSubmit hooks run via `node`.

### A.9 Results layout, pass/fail, tokens, cost [V]
- Layout: `<jobs-dir>/<job-name>/` contains `config.json`, `lock.json`, `result.json` (JobResult with `stats.{n_input_tokens,n_cache_tokens,n_output_tokens,cost_usd}` totals) and `job.log`. It has one dir per trial, `<task-name[:32]>__<7-char id>/` (harbor@v0.23.0:src/harbor/job.py:640-655; models/trial/config.py:545-548; models/job/result.py:38-41).
- Trial dir (models/trial/paths.py:84-106): `result.json` (the docstring says "results.json" but the code uses `result.json`, paths.py:289-291), `config.json`, `lock.json`, `trial.log`, `exception.txt`, `agent/` (claude-code: `claude-code.txt` stream-json, `sessions/` = CLAUDE_CONFIG_DIR with the jsonl transcript, `trajectory.json` in ATIF; codex: `codex.txt`, `sessions/`, `trajectory.json`), `verifier/` (`reward.txt` or `reward.json`, test stdout and stderr), `artifacts/`.
- Pass/fail: `result.json → verifier_result.rewards.reward`. It comes from `reward.txt`, read as `{"reward": float}` (verifier/verifier.py:68-87).
- Tokens and cost: `result.json → agent_result.{n_input_tokens, n_cache_tokens, n_output_tokens, cost_usd}` (models/agent/context.py:21-33). `n_input_tokens` **includes** cached tokens.
  - claude-code: prompt = input + cache_read + cache_creation (claude_code.py:842-845). `n_cache_tokens` = cache reads only. Cache writes are in `agent/trajectory.json → final_metrics.extra.total_cache_creation_input_tokens`. **Cost = Claude Code's own `total_cost_usd`** from the final stream-json `result` event (claude_code.py:944-973, 1559-1564), with a LiteLLM estimate as fallback (`cost_source: litellm_estimate`).
  - codex: tokens come from the last `token_count` event's `total_token_usage` (input, cached_input, output, reasoning_output). **Codex does not report cost.** Harbor prices each call with LiteLLM's `model_cost` table (codex.py:722-779, 1090-1136). The LiteLLM bundled with harbor 0.23.0 (1.102.1) has **no entry for `gpt-6-*` except `gpt-6-astra`**. By default LiteLLM fetches a remote cost map at import, so it may still resolve [U]. If a model is unknown, `cost_usd` is `None`. **Recompute cost yourself from tokens** for every Codex trial.
  - opencode: sums `cost` and `tokens` from `step_finish` events of `opencode run --format=json` (opencode.py:260-340).
- Viewer: `harbor view <jobs-dir>` (docs `core-concepts/results/view-job-results.mdx`).

### A.10 Local Docker vs cloud [V]
- `-e docker` is the default and needs no account. `-e daytona` needs `DAYTONA_API_KEY`, and `-e modal` needs Modal auth (README on PyPI). `--mounts` is Docker-only. For cloud envs use the upload-in-`setup()` subclass.
- `-e apple-container` exists and requires Apple silicon (environments/apple_container.py:38-40). Not evaluated.

---

## B. macOS arm64 + local Docker

- Local daemon: Docker Desktop **4.68.0**, engine 29.3.1, `linux/arm64`, 10 CPUs, 8.2 GB RAM, kernel 6.12.76-linuxkit (`docker version`, `docker info`). [V]
- Harbor builds Dockerfile-based envs for the daemon's native platform (`docker version --format {{.Server.Os}}/{{.Server.Arch}}`, environments/docker/utils.py:35-54). But **if `task.toml` sets `docker_image`, Harbor pulls that prebuilt image unless `--force-build`** (environments/definition.py:26-36). [V]
- **All 89 Terminal-Bench-2 task images are amd64-only.** Docker Hub API: 89/89 are `alexgshaw/<task>:20251031` with a single `amd64` manifest. Median compressed size is 149 MB, total about 49 GB. Four exceed 2 GB: mteb-leaderboard 8.8 GB, mteb-retrieve 8.8 GB, hf-model-inference 6.2 GB, pytorch-model-recovery 6.1 GB. **Exclude those four** with `-x`. [V]
- Emulation works on this machine. `docker run --platform linux/amd64 alpine uname -m` gives `x86_64`. A micro-benchmark (alpine, same loop):
  - pure shell arithmetic: 0.35 s arm64 vs 0.55 s amd64 (**1.6x slower**)
  - 300 process spawns: 0.10 s vs 0.64 s (**~6x slower**)
  Expect slower agent install (npm, bootstrap), slower test suites and a higher timeout risk. Agent **tokens and cost** are unaffected, but wall-clock timeouts can flip outcomes. [V, measured]
- `--force-build` rebuilds natively for arm64 from each task's `environment/Dockerfile`. This is faster at runtime, but some tasks are x86-specific (harbor issue #2758 describes an x86-only task silently scoring 0 on arm64). Use one platform consistently across all arms, and record it. Harbor does not record the platform yet (#2758, open). [V]
- Known macOS issues:
  - `network_mode = "allowlist"` and static `"no-network"` tasks fail on Docker Desktop's LinuxKit kernel before **Docker Desktop 4.86.0**, because of nftables `NFT_FIB_INET` (#2527, #2593; commenters confirm the fix with 4.86/4.87). **This machine runs 4.68, so upgrade Docker Desktop, or avoid such tasks.** TB2 tasks use `allow_internet = true` (checked: fix-git, regex-log, log-summary-date-ranges). [V]
  - Egress sidecar build-lock deadlock with `-n > 1` (#2348). The upstream filelock fix landed, and Harbor pins filelock 3.29.4 [V from the issue thread]. It only matters for allowlist tasks.
- Resources: TB2 tasks declare `cpus=1, memory_mb=2048`. With 8 GB given to Docker, use **`-n 3`**, or at most 4. The disk has room for the non-huge TB2 images (about 13 GB compressed without the four big ones) [U: estimate].

---

## C. OpenCode (deferred; short)

- The repo is **anomalyco/opencode**. `gh api repos/sst/opencode` redirects to `anomalyco/opencode`. npm `opencode-ai` latest is 1.18.32 (2026-09-21). [V]
- Local machine: **OpenCode is not installed.** `which opencode` gives "opencode not found", even in an interactive zsh. There is no npm global and no `~/.opencode` or `~/.config/opencode`; only a Zed agent-registry icon exists. `opencode --version` "printed nothing" because the shell's "command not found" went to stderr. [V]
- Harbor runs: `opencode --model=<provider/model> run --format=json --thinking --dangerously-skip-permissions -- '<instr>'` (opencode.py:541-551). Skills go to `~/.config/opencode/skills`. Config overlay goes to `~/.config/opencode/opencode.json` via `--ak opencode_config='{...}'`. `OPENROUTER_API_KEY` is passed through for `-m openrouter/...` (model_connection.py:111-114). Cost comes from `step_finish` events. [V]
- Skill dirs: `.opencode/skills`, `.claude/skills`, `.agents/skills` (project), plus `~/.config/opencode/skills`, `~/.claude/skills`, `~/.agents/skills` (https://opencode.ai/docs/skills). AGENTS.md is loaded, with CLAUDE.md as fallback, plus `~/.config/opencode/AGENTS.md`. `OPENCODE_DISABLE_CLAUDE_CODE*` env vars turn off .claude compat (https://opencode.ai/docs/rules). [V docs]

## D. Open-weight models on OpenRouter (deferred; raw snapshot only)

From `https://openrouter.ai/api/v1/models` (460 models, fetched 2026-09-25). Prices are $/MTok as input / cache-read / output. All support `tools`. **Open-weight status and leaderboard standing are not checked [U].**
- deepseek/deepseek-v4.1-flash: 0.30 / 0.006 / 1.20, 1M ctx
- z-ai/glm-5.3: 1.40 / 0.26 / 4.40, 1.3M
- z-ai/glm-5.3-flash: 0.045 / 0.029 / 0.60
- moonshotai/kimi-k3: 0.884 / 0.33 / 10.54
- minimax/minimax-m3: 0.30 / 0.06 / 1.20
- qwen/qwen3.8-27b: 0.42 / 0.085 / 3.00

No recommendation was made. Revisit when the OpenCode arm is scheduled.

---

## E. Claude Code headless on an API key

- Harbor already does the right thing (A.4): `ANTHROPIC_API_KEY` is forwarded, `--print --output-format=stream-json --verbose`, `--permission-mode=bypassPermissions` plus `IS_SANDBOX=1` (so root in a container is accepted), and `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1`. The model goes via `ANTHROPIC_MODEL`, and effort via `--effort`. [V]
- Outside Harbor, the equivalent is: `ANTHROPIC_API_KEY=... IS_SANDBOX=1 CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1 claude -p --model claude-sonnet-5 --effort medium --permission-mode bypassPermissions --output-format stream-json --verbose "<prompt>"`. Flags come from local `claude --help` 2.1.280. [V]
- Useful knobs:
  - `--max-budget-usd` (`--ak max_budget_usd=2`) is a per-trial hard stop.
  - `--max-turns` (`--ak max_turns=`).
  - `CLAUDE_CODE_SUBAGENT_MODEL` pins the subagent model.
  - `CLAUDE_CODE_DISABLE_CLAUDE_MDS=1`.
  - `--exclude-dynamic-system-prompt-sections` improves cross-session cache reuse [V env-vars.md / --help]. Not exposed by Harbor.
- Caveat: `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` also disables feature-flag fetching (env-vars.md line 513). That holds in all arms, so it is fine for relative comparisons.
- **`claude plugin eval`** (local 2.1.280 `--help`; https://code.claude.com/docs/en/plugin-evals.md):
  - It runs cases (`prompt.md` + `case.yaml` + `graders/*.md`) with `--runs N` (default 3), `--ablation with-without` (a built-in no-plugin baseline arm), `-j` concurrency up to 8, `--max-cost-usd`, `--json`, `--model`, and `--judge-model`.
  - It runs on the host under Claude Code's OS sandbox, not Docker. **"There are no custom-code graders"** (plugin-evals.md line 217). Graders are llm, regex, file checks and `tool_used`/`tool_order`. So it cannot run Harbor's pytest verifiers, and it has no placebo arm.
  - What we can reuse:
    - its `tool_used: Skill` "plugin-fired" indicator idea (compute it from Harbor trajectories instead);
    - `claude plugin details` for always-on token cost, used in length matching;
    - optionally, a cheap sanity check that a plugin loads and fires before paying for Harbor runs.

---

## Codex (model, pricing, auth; added per scope change)

<!-- CODEX-PRICING-PLACEHOLDER -->

---

## Token and cost estimates per trial

<!-- TOKENS-PLACEHOLDER -->

---

## Recommended pipeline

<!-- PIPELINE-PLACEHOLDER -->
