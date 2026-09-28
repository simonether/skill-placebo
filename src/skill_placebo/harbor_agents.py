"""Harbor agent subclasses used by the runner (docs/research/2026-09-25-harness-infra.md, A.8).

CodexPlugins installs plugins into Codex inside the container and lets their hooks run:
  --ae SP_CODEX_MARKETPLACES=/opt/plugins/a:/opt/plugins/b   marketplaces to add (paths in the container)
  --ae SP_CODEX_PLUGINS=name@marketplace,...                  plugins to enable
Harbor does not pass --dangerously-bypass-hook-trust itself; without it Codex skips plugin hooks
until a human trusts them, which cannot happen in a headless run.
"""
import shlex

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
