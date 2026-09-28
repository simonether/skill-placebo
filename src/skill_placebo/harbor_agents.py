"""Harbor agent subclasses used by the runner (docs/research/2026-09-25-harness-infra.md, A.8).

ClaudeCodeArms prepares $CLAUDE_CONFIG_DIR identically in every arm, then applies the arm:
  - marker files that stop ponytail and caveman from telling the agent to offer a statusline
    setup (they fire in every fresh container otherwise), created in ALL arms;
  - the i-have-adhd always-on flag (its documented always-on install), created in ALL arms:
    only that plugin's hook reads it, so other arms are unaffected;
  - --ae SP_CLAUDE_MD=<path in container>: copied to $CLAUDE_CONFIG_DIR/CLAUDE.md, the user-level
    memory file (karpathy-skills and its placebo).
Plugins themselves load through CLAUDE_CODE_PLUGIN_DIRS (--ae), no code needed.

CodexPlugins installs plugins into Codex inside the container and lets their hooks run:
  --ae SP_CODEX_MARKETPLACES=/opt/plugins/a:/opt/plugins/b   marketplaces to add (paths in the container)
  --ae SP_CODEX_PLUGINS=name@marketplace,...                  plugins to enable
Harbor does not pass --dangerously-bypass-hook-trust itself; without it Codex skips plugin hooks
until a human trusts them, which cannot happen in a headless run.
"""
import shlex

from harbor.agents.installed.claude_code import ClaudeCode
from harbor.agents.installed.codex import Codex

_NVM = "if [ -s ~/.nvm/nvm.sh ]; then . ~/.nvm/nvm.sh; fi; "


class CodexPlugins(Codex):
    def _plugin_cmds(self) -> list[str]:
        cmds = [
            f"{_NVM}codex plugin marketplace add {shlex.quote(s)}"
            for s in filter(None, (self._get_env("SP_CODEX_MARKETPLACES") or "").split(":"))
        ]
        cmds += [
            f"{_NVM}codex plugin add {shlex.quote(p)}"
            for p in filter(None, (self._get_env("SP_CODEX_PLUGINS") or "").split(","))
        ]
        return cmds

    def _build_register_skills_command(self):
        # Appended to the setup that runs after config.toml is uploaded, with CODEX_HOME set.
        parts = [p for p in [super()._build_register_skills_command(), *self._plugin_cmds()] if p]
        return " && ".join(f"( {p} )" for p in parts) if parts else None

    def build_cli_flags(self):
        flags = super().build_cli_flags()
        if self._plugin_cmds():
            return f"{flags} --dangerously-bypass-hook-trust".strip()
        return flags


MARKERS = (".ponytail-statusline-nudged", ".caveman-nudge-shown", ".i-have-adhd-always")


class ClaudeCodeArms(ClaudeCode):
    def _build_register_skills_command(self):
        parts = [super()._build_register_skills_command()]
        parts.append("mkdir -p $CLAUDE_CONFIG_DIR && " + " && ".join(f"touch $CLAUDE_CONFIG_DIR/{m}" for m in MARKERS))
        claude_md = self._get_env("SP_CLAUDE_MD")
        if claude_md:
            parts.append(f"cp {shlex.quote(claude_md)} $CLAUDE_CONFIG_DIR/CLAUDE.md")
        parts = [p for p in parts if p]
        return " && ".join(f"( {p} )" for p in parts)
