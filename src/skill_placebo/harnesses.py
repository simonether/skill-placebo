"""Pinned harness configurations (METHOD.md section 5).

Logins come from the owner's subscriptions, never from the parent session or the host's own
Claude/Codex logins:
  Claude Code: CLAUDE_CODE_OAUTH_TOKEN from .secrets/api.env (made with `claude setup-token`),
               CLAUDE_FORCE_OAUTH=1 so Harbor uses it.
  Codex:       CODEX_AUTH_JSON_PATH -> .secrets/codex-home/auth.json (separate device login).
               CODEX_FORCE_AUTH_JSON is deliberately NOT set: in Harbor it means the host's
               ~/.codex/auth.json.
"""
from .runner import ROOT, Harness

CODEX_AUTH_JSON = ROOT / ".secrets" / "codex-home" / "auth.json"

CLAUDE_CODE = Harness(
    name="claude-code",
    agent="claude-code",
    model="anthropic/claude-opus-5-5",
    kwargs={
        "version": "2.1.282",
        "reasoning_effort": "EFFORT_TBD",  # Claude Code's default for Opus 5.5, passed explicitly
        "disallowed_tools": ["WebSearch", "WebFetch"],
    },
    creds=("CLAUDE_CODE_OAUTH_TOKEN",),
    extra_env={"CLAUDE_FORCE_OAUTH": "1"},
)

CODEX = Harness(
    name="codex",
    agent="skill_placebo.harbor_agents:CodexPlugins",
    model="openai/gpt-6-sol",
    kwargs={
        "version": "0.157.0",
        "reasoning_effort": "medium",
        "web_search": "disabled",
    },
    creds=(),
    extra_env={"CODEX_AUTH_JSON_PATH": str(CODEX_AUTH_JSON)},
)

HARNESSES = {h.name: h for h in (CLAUDE_CODE, CODEX)}
