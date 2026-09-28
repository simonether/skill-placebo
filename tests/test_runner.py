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


def test_run_batch_refuses_placeholders(tmp_path):
    import pytest
    from skill_placebo.runner import run_batch
    h = Harness("claude-code", "claude-code", "m", kwargs={"reasoning_effort": "EFFORT_TBD"})
    with pytest.raises(SystemExit):
        run_batch([], h, {}, tmp_path, units_budget=1.0)


def test_real_run_requires_usd_budget(tmp_path):
    import pytest
    from skill_placebo.runner import run_batch
    h = Harness("claude-code", "claude-code", "m")
    with pytest.raises(SystemExit):
        run_batch([], h, {}, tmp_path)


def test_ledger_window(tmp_path, monkeypatch):
    import skill_placebo.runner as r
    monkeypatch.setattr(r, "ledger_path", lambda h: tmp_path / f"ledger-{h}.jsonl")
    (tmp_path / "ledger-cc.jsonl").write_text(
        json.dumps({"ts": "2026-09-28T10:00:00Z", "units": 1.5e6}) + "\n"
        + json.dumps({"ts": "2026-09-30T10:00:00Z", "units": 2.0e6}) + "\n")
    assert r.ledger_spent("cc", None) == 3.5e6
    assert r.ledger_spent("cc", "2026-09-29T00:00:00Z") == 2.0e6


def test_pace_wait(tmp_path, monkeypatch):
    import time as _t
    import skill_placebo.runner as r
    monkeypatch.setattr(r, "ledger_path", lambda h: tmp_path / f"ledger-{h}.jsonl")
    now = _t.time()
    rows = [(now - 4 * 3600, 50e6), (now - 1 * 3600, 30e6)]  # 80M in the last 5 h
    (tmp_path / "ledger-cc.jsonl").write_text("".join(json.dumps({"ts": r.utc_iso(t), "units": u}) + "\n" for t, u in rows))
    w = r.pace_wait_seconds("cc", 75e6, now=now)
    assert 3500 < w < 3700  # the 50M entry leaves the window in ~1 h
    assert r.pace_wait_seconds("cc", 100e6, now=now) == 0.0


def test_units_formula():
    from skill_placebo.collect import units_from_tokens
    # 1000 total input of which 600 cache read and 100 cache write -> 300 uncached; 50 output
    assert units_from_tokens(1000, 600, 100, 50) == 300 + 125 + 60 + 250


def test_rate_limit_event_allowed_is_not_a_stop(tmp_path):
    d = tmp_path / "trial" / "agent"
    d.mkdir(parents=True)
    ok = {"type": "rate_limit_event", "rate_limit_info": {"status": "allowed", "isUsingOverage": False,
          "unifiedWindows": {"five_hour": {"utilization": 0.13}, "seven_day": {"utilization": 0.04, "resetsAt": 1}}}}
    (d / "claude-code.txt").write_text(json.dumps(ok))
    assert limit_hits(tmp_path / "trial") == []
    from skill_placebo.runner import claude_windows
    assert claude_windows(tmp_path / "trial") == {"five_hour": 0.13, "seven_day": 0.04, "seven_day_resets": 1}  # regression: "allowed" never stops
    warn = dict(ok, rate_limit_info=dict(ok["rate_limit_info"], status="allowed_warning"))
    (d / "claude-code.txt").write_text(json.dumps(warn))
    assert limit_hits(tmp_path / "trial")


def test_plugin_hook_text_with_401_does_not_stop(tmp_path):
    """Regression (29.09 pilot): i-have-adhd's SessionStart hook injects an example with '401' and 'auth'."""
    d = tmp_path / "trial" / "agent"
    d.mkdir(parents=True)
    ev = {"type": "system", "subtype": "hook_response", "hook_event": "SessionStart",
          "output": 'Good: "Test fails at `auth.spec.ts:42`: expected 200, got 401. Cause: missing auth header."'}
    (d / "claude-code.txt").write_text(json.dumps(ev) + "\n" + json.dumps({"type": "result", "is_error": False, "result": "OK"}))
    assert limit_hits(tmp_path / "trial") == []
    api_err = {"type": "result", "is_error": True, "api_error_status": 429, "result": "API Error: 429 rate_limit_error"}
    (d / "claude-code.txt").write_text(json.dumps(api_err))
    assert limit_hits(tmp_path / "trial")


def test_infra_failure_classification(tmp_path):
    from skill_placebo.runner import infra_failure
    j = tmp_path / "job"
    (j / "t1").mkdir(parents=True)
    (j / "t1" / "result.json").write_text(json.dumps({"exception_info": {"exception_type": "AgentSetupTimeoutError"}}))
    assert infra_failure(j) == "AgentSetupTimeoutError"
    (j / "t1" / "result.json").write_text(json.dumps({"exception_info": {"exception_type": "VerifierTimeoutError"}}))
    assert infra_failure(j) is None
    (j / "t1" / "result.json").write_text(json.dumps({"exception_info": {"exception_type": "RuntimeError", "exception_message": "Docker compose command failed ... 429"}}))
    assert infra_failure(j) == "RuntimeError"
