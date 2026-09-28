from skill_placebo.harnesses import CLAUDE_CODE, CODEX, CODEX_AUTH_JSON
from skill_placebo.runner import clean_env


def test_codex_uses_dedicated_login_never_host():
    env = clean_env(CODEX, {})
    assert env["CODEX_AUTH_JSON_PATH"] == str(CODEX_AUTH_JSON)
    assert ".secrets/codex-home/auth.json" in env["CODEX_AUTH_JSON_PATH"]
    assert "CODEX_FORCE_AUTH_JSON" not in env  # in Harbor this means the host's ~/.codex/auth.json
    assert "OPENAI_API_KEY" not in env


def test_claude_uses_benchmark_token_only(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "should-not-leak")
    env = clean_env(CLAUDE_CODE, {"CLAUDE_CODE_OAUTH_TOKEN": "t"})
    assert env["CLAUDE_FORCE_OAUTH"] == "1"
    assert "ANTHROPIC_API_KEY" not in env and "ANTHROPIC_BASE_URL" not in env


def test_web_tools_disabled_in_both():
    assert set(CLAUDE_CODE.kwargs["disallowed_tools"]) == {"WebSearch", "WebFetch"}
    assert CODEX.kwargs["web_search"] == "disabled"
