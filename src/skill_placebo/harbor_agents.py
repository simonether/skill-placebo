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
        # Same statusline/always-on markers as ClaudeCodeArms, in ~/.claude where hooks look without
        # CLAUDE_CONFIG_DIR; created in every Codex arm.
        markers = "mkdir -p ~/.claude && " + " && ".join(f"touch ~/.claude/{m}" for m in MARKERS)
        parts = [p for p in [super()._build_register_skills_command(), markers, *self._plugin_cmds()] if p]
        return " && ".join(f"( {p} )" for p in parts)

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


# ---------------------------------------------------------------------------------------------
# Scripted approval turn (METHOD.md section 5), identical in every arm of both harnesses.
# After the agent's main run, if its final message ends in a question (a '?' in its last 200
# characters) the harness sends APPROVAL_TEXT in the same session, at most MAX_APPROVALS times.
# It is appended to the main shell command, because Harbor's Codex agent deletes CODEX_HOME (and
# with it the login and the session) right after the main command returns.
# ---------------------------------------------------------------------------------------------
import re as _re

APPROVAL_TEXT = (
    "If you are waiting for approval to continue the task, you have it: proceed with your best "
    "judgment. If the task is complete, reply DONE."
)
MAX_APPROVALS = 2

# node: exit 0 when the last completed turn ended in a question, 1 otherwise (errors, no text).
CHECK_JS = r"""
const fs = require('fs'); const [kind, file] = process.argv.slice(1);
let lines = []; try { lines = fs.readFileSync(file, 'utf8').split('\n'); } catch (e) { process.exit(1); }
let text = null, err = false;
for (const l of lines) {
  let e; try { e = JSON.parse(l); } catch (_) { continue; }
  if (kind === 'claude' && e.type === 'result') { text = e.result || ''; err = !!e.is_error; }
  if (kind === 'codex') {
    if (e.type === 'turn.started') { text = null; err = false; }
    if (e.type === 'turn.failed') err = true;
    if (e.type === 'item.completed' && e.item && e.item.type === 'agent_message') text = e.item.text || '';
  }
}
if (err || !text) process.exit(1);
process.exit(text.slice(-200).includes('?') ? 0 : 1);
""".strip()


def approval_loop(kind: str, resume_cmd: str, log_file: str) -> str:
    """Shell appended after the main command. resume_cmd reads the approval text from $SP_APPROVAL."""
    turns = f"$(dirname {log_file})/approval_turns.txt"
    return (
        f"_sp_n=0; while [ $_sp_n -lt {MAX_APPROVALS} ] && node -e \"$SP_CHECK\" {kind} {log_file}; do "
        f"_sp_n=$((_sp_n+1)); {resume_cmd}; done; echo $_sp_n > {turns}; true"
    )


_CLAUDE_MAIN = _re.compile(r"(claude --verbose --output-format=stream-json .*?)--print 2>&1 \| tee (\S+)", _re.S)
_CODEX_MAIN = _re.compile(r"codex exec (--dangerously-bypass-approvals-and-sandbox .*?)-- .* 2>&1 </dev/null \| tee (\S+)", _re.S)


def claude_followup(command: str) -> str | None:
    m = _CLAUDE_MAIN.search(command)
    if not m or "--continue" in command:
        return None
    flags, log = m.group(1), m.group(2)
    resume = f'printf "%s" "$SP_APPROVAL" | {flags}--continue --print 2>&1 | tee -a {log}'
    return approval_loop("claude", resume, log)


def codex_followup(command: str) -> str | None:
    m = _CODEX_MAIN.search(command)
    if not m or "exec resume" in command:
        return None
    flags, log = m.group(1), m.group(2)
    resume = f'{_NVM}codex exec resume --last {flags}-- "$SP_APPROVAL" 2>&1 </dev/null | tee -a {log}'
    return approval_loop("codex", resume, log)


async def _exec_with_approval(agent, super_exec, followup, environment, command, env=None, **kw):
    extra = followup(command)
    if extra:
        command = f"{command} ; {extra}"
        env = {**(env or {}), "SP_APPROVAL": APPROVAL_TEXT, "SP_CHECK": CHECK_JS}
    return await super_exec(environment, command=command, env=env, **kw)


async def _claude_exec(self, environment, command, env=None, **kw):
    return await _exec_with_approval(self, super(ClaudeCodeArms, self).exec_as_agent, claude_followup, environment, command, env, **kw)


async def _codex_exec(self, environment, command, env=None, **kw):
    return await _exec_with_approval(self, super(CodexPlugins, self).exec_as_agent, codex_followup, environment, command, env, **kw)


ClaudeCodeArms.exec_as_agent = _claude_exec
CodexPlugins.exec_as_agent = _codex_exec
