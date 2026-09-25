import json

from skill_placebo.runner import Arm, Harness, clean_env, limit_hits, plan


def test_plan_blocks_cover_every_pair_once_per_block():
    arms = [Arm("baseline"), Arm("placebo-a"), Arm("skill-x")]
    tr = plan(["t1", "t2"], arms, "claude-code", n=3, seed=7)
    assert len(tr) == 18
    for b in range(3):
        pairs = {(t.task, t.arm) for t in tr if t.block == b}
        assert len(pairs) == 6
    assert tr != plan(["t1", "t2"], arms, "claude-code", n=3, seed=8)
    assert [t.job_name for t in tr] == [t.job_name for t in plan(["t1", "t2"], arms, "claude-code", n=3, seed=7)]


def test_clean_env_drops_parent_session(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_BASE_URL", "http://proxy")
    monkeypatch.setenv("CLAUDE_CODE_OAUTH_TOKEN", "parent-token")
    h = Harness("claude-code", "claude-code", "anthropic/claude-sonnet-5",
                creds=("CLAUDE_CODE_OAUTH_TOKEN",), extra_env={"CLAUDE_FORCE_OAUTH": "1"})
    env = clean_env(h, {"CLAUDE_CODE_OAUTH_TOKEN": "bench-token"})
    assert "ANTHROPIC_BASE_URL" not in env
    assert env["CLAUDE_CODE_OAUTH_TOKEN"] == "bench-token"
    assert env["HARBOR_TELEMETRY"] == "0"


def test_limit_hits_ignores_task_content_but_catches_events(tmp_path):
    d = tmp_path / "trial" / "agent"
    d.mkdir(parents=True)
    lines = [
        {"type": "user", "message": {"content": "server returned 429 Too Many Requests"}},
        {"type": "assistant", "message": {"content": "handle the rate limit in retry()"}},
        {"type": "result", "is_error": False, "result": "done"},
    ]
    (d / "claude-code.txt").write_text("\n".join(json.dumps(x) for x in lines))
    assert limit_hits(tmp_path / "trial") == []
    lines.append({"type": "rate_limit_event", "rate_limit_info": {"status": "allowed_warning"}})
    (d / "claude-code.txt").write_text("\n".join(json.dumps(x) for x in lines))
    assert limit_hits(tmp_path / "trial")


def test_limit_hits_catches_auth_failure(tmp_path):
    d = tmp_path / "trial" / "agent"
    d.mkdir(parents=True)
    ev = {"type": "result", "is_error": True, "result": "Not logged in · Please run /login"}
    (d / "claude-code.txt").write_text(json.dumps(ev))
    assert limit_hits(tmp_path / "trial")


def test_exception_txt_task_text_does_not_stop(tmp_path):
    t = tmp_path / "trial"
    t.mkdir()
    (t / "exception.txt").write_text("NonZeroAgentExitCodeError: printf '%s' 'Missing X-Team-ID must return 401 Unauthorized and 429 on quota' | claude")
    assert limit_hits(t) == []
    (t / "exception.txt").write_text("failed to resolve source metadata for docker.io/library/python: unexpected status from HEAD request to https://registry-1.docker.io/v2/x: 429 Too Many Requests")
    assert limit_hits(t)
