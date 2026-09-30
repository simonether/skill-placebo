import json
from pathlib import Path

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


def test_arm_not_applied_detects_missing_plugin(tmp_path):
    from skill_placebo.runner import Arm, arm_not_applied
    job = tmp_path / "job"
    t = job / "trial"
    (t / "agent").mkdir(parents=True)
    (t / "result.json").write_text("{}")
    arm = Arm("placebo-cc-5", ("--ae", "CLAUDE_CODE_PLUGIN_DIRS=/opt/plugins/placebo-cc-5"))
    init = {"type": "system", "subtype": "init", "plugins": [{"name": "agents-md", "path": "builtin"}]}
    (t / "agent" / "claude-code.txt").write_text(json.dumps(init))
    assert arm_not_applied(job, arm)
    init["plugins"].append({"name": "session-notes-cc-5", "path": "/opt/plugins/placebo-cc-5"})
    (t / "agent" / "claude-code.txt").write_text(json.dumps(init))
    assert arm_not_applied(job, arm) is None
    assert arm_not_applied(job, Arm("baseline")) is None


def test_arm_hash_dirs_and_change(tmp_path):
    from skill_placebo.runner import Arm, arm_host_dirs, tree_hash
    d = tmp_path / "placebo-cc-5"
    d.mkdir()
    (d / "a.txt").write_text("x")
    mounts = json.dumps([{"type": "bind", "source": str(d), "target": "/opt/plugins/placebo-cc-5", "read_only": True}])
    arm = Arm("placebo-cc-5", ("--ae", "CLAUDE_CODE_PLUGIN_DIRS=/opt/plugins/placebo-cc-5"))
    assert arm_host_dirs(arm, mounts) == [d]
    h1 = tree_hash([d])
    (d / "a.txt").write_text("y")
    assert tree_hash([d]) != h1
    assert tree_hash(arm_host_dirs(Arm("baseline"), mounts)) is None


def test_derived_task_points_environment_at_snapshot(tmp_path):
    from skill_placebo.runner import derived_task

    src = tmp_path / "task"
    (src / "environment").mkdir(parents=True)
    (src / "environment" / "Dockerfile").write_text("FROM python:3.11-slim\n")
    (src / "task.toml").write_text('version = "1.0"\n\n[verifier]\ntimeout_sec = 180.0\n\n[environment]\n'
                                   '# docker_image removed by skill-placebo\ndocker_image = "old"\nbuild_timeout_sec = 600.0\n')
    out = derived_task(src, "skill-placebo-snapshot:x__env", tmp_path / "d" / "task")
    toml = (out / "task.toml").read_text()
    assert 'docker_image = "skill-placebo-snapshot:x__env"' in toml and '"old"' not in toml
    assert "timeout_sec = 180.0" in toml and (out / "environment" / "Dockerfile").exists()
    assert (src / "task.toml").read_text().count("docker_image") == 2  # source untouched


def test_verifier_rerun_without_snapshot_leaves_a_failed_trial(tmp_path):
    from skill_placebo.runner import verifier_rerun

    t = tmp_path / "job" / "trial__x"
    t.mkdir(parents=True)
    (t / "result.json").write_text(json.dumps({"task_name": "t", "exception_info": {"exception_type": "VerifierTimeoutError"}}))
    (rec,) = verifier_rerun(tmp_path / "job", tmp_path / "task", None)
    assert rec["outcome"] == "no snapshot"
    assert json.loads((t / "verifier_rerun.json").read_text())["outcome"] == "no snapshot"


def test_verifier_rerun_ignores_other_trials(tmp_path):
    from skill_placebo.runner import verifier_rerun

    t = tmp_path / "job" / "trial__x"
    t.mkdir(parents=True)
    (t / "result.json").write_text(json.dumps({"task_name": "t", "verifier_result": {"rewards": {"reward": 0.0}}}))
    assert verifier_rerun(tmp_path / "job", tmp_path / "task", None) == []
    assert not (t / "verifier_rerun.json").exists()


def test_snapshot_tag_matches_compose_project():
    from skill_placebo.harbor_launch import snapshot_tag

    assert snapshot_tag("fix_async_worker_queue__XfygSNC") == "skill-placebo-snapshot:fix_async_worker_queue__xfygsnc__env"


def test_harbor_cmd_uses_launcher_only_with_snapshot():
    from skill_placebo.runner import Arm, Harness, Trial, harbor_cmd

    t = Trial(0, 0, "claude-code", "baseline", "calibration/say-ok")
    h = Harness("claude-code", "a", "m")
    plain = harbor_cmd(t, h, Arm("baseline"), Path("/tmp/j"), None)
    snap = harbor_cmd(t, h, Arm("baseline"), Path("/tmp/j"), None, snapshot=True)
    assert "harbor" in plain and "skill_placebo.harbor_launch" not in plain
    assert snap[snap.index("-m") + 1] == "skill_placebo.harbor_launch" and snap[snap.index("-m") + 2] == "run"


def test_disk_state_thresholds():
    from skill_placebo.runner import disk_state

    assert disk_state(23.0, 10, 6) == "go"
    assert disk_state(9.9, 10, 6) == "pause"
    assert disk_state(5.9, 10, 6) == "stop"
    assert disk_state(1.0, None, None) == "go"


def test_running_batches_can_exclude_own(tmp_path, monkeypatch):
    import os
    from skill_placebo import runner

    monkeypatch.setattr(runner, "ROOT", tmp_path)
    own = tmp_path / "jobs" / "main" / "claude-code"
    own.mkdir(parents=True)
    (own / ".lock").write_text(str(os.getpid()))
    assert runner.running_batches() == [own]
    assert runner.running_batches(exclude=own) == []


def test_run_batch_pauses_then_stops_on_low_disk(tmp_path, monkeypatch, capsys):
    from skill_placebo import runner

    monkeypatch.setattr(runner, "ROOT", tmp_path)
    monkeypatch.setattr(runner, "sweep_snapshots", lambda own=None: None)
    free = iter([8.0, 8.0, 3.0])
    monkeypatch.setattr(runner, "host_free_gib", lambda path="/": next(free))
    started = []
    monkeypatch.setattr(runner.subprocess, "run", lambda *a, **k: started.append(a))
    trials = runner.plan(["t1"], [runner.Arm("baseline")], "test-h", n=1, seed=1)
    state = runner.run_batch(trials, runner.Harness("test-h", "a", "m"), {"baseline": runner.Arm("baseline")},
                             tmp_path / "jobs" / "b", units_budget=1e9, concurrency=1,
                             disk_pause_gib=10, disk_stop_gib=6, disk_check_s=0)
    out = capsys.readouterr().out
    assert "disk pause" in out and state.stopped.startswith("host disk free 3.0 GiB")
    assert started == []  # no trial started


def test_interrupted_attempt_is_recorded_once_with_its_tokens(tmp_path, monkeypatch):
    from skill_placebo import runner

    monkeypatch.setattr(runner, "ROOT", tmp_path)
    (tmp_path / "jobs").mkdir()
    job = tmp_path / "jobs" / "b00-0069__claude-code__placebo-cc-5__fix_async_worker_queue"
    t = job / "fix_async_worker_queue__x"
    (t / "agent").mkdir(parents=True)
    (t / "config.json").write_text("{}")
    (job / "result.json").write_text("{}")  # Harbor's job-level result exists; the trial's does not
    ev = lambda mid, out: json.dumps({"type": "assistant", "message": {"id": mid, "usage": {
        "input_tokens": 10, "cache_creation_input_tokens": 100, "cache_read_input_tokens": 1000, "output_tokens": out}}})
    (t / "agent" / "claude-code.txt").write_text("\n".join([ev("m1", 5), ev("m1", 50), ev("m2", 20), "not json"]))
    rec = runner.record_interrupted(job, "claude-code", "anthropic/claude-opus-5-5")
    assert rec["phase"] == "agent or setup" and rec["messages"] == 2
    assert rec["n_output"] == 70 and rec["n_cached"] == 2000 and rec["n_input"] == 2220
    (row,) = [json.loads(x) for x in runner.ledger_path("claude-code").read_text().splitlines()]
    assert row["exception"] == "Interrupted" and row["infra_failure"] == 1 and row["arm"] == "placebo-cc-5"
    assert row["units"] == 20 * 1.0 + 200 * 1.25 + 2000 * 0.1 + 70 * 5
    assert runner.record_interrupted(job, "claude-code", "anthropic/claude-opus-5-5") is None  # once


def test_finished_attempt_is_not_interrupted(tmp_path):
    from skill_placebo.runner import record_interrupted

    t = tmp_path / "job" / "trial__x"
    t.mkdir(parents=True)
    (t / "result.json").write_text("{}")
    assert record_interrupted(tmp_path / "job", "claude-code", "m") is None


def _session(tmp_path, version, model):
    t = tmp_path / "job" / "trial__x" / "agent"
    t.mkdir(parents=True, exist_ok=True)
    (t / "claude-code.txt").write_text(json.dumps({"type": "system", "subtype": "init",
                                                    "claude_code_version": version, "model": model}) + "\n")
    return tmp_path / "job"


def test_pin_mismatch_claude(tmp_path):
    from skill_placebo.harnesses import CLAUDE_CODE
    from skill_placebo.runner import pin_mismatch

    assert pin_mismatch(_session(tmp_path / "a", "2.1.282", "claude-opus-5-5"), CLAUDE_CODE) is None
    assert "2.1.290" in pin_mismatch(_session(tmp_path / "b", "2.1.290", "claude-opus-5-5"), CLAUDE_CODE)
    assert "claude-sonnet-5" in pin_mismatch(_session(tmp_path / "c", "2.1.282", "claude-sonnet-5"), CLAUDE_CODE)


def test_pin_mismatch_codex(tmp_path):
    from skill_placebo.harnesses import CODEX
    from skill_placebo.runner import pin_mismatch

    d = tmp_path / "job" / "trial__x" / "agent" / "sessions"
    d.mkdir(parents=True)
    rollout = lambda v, m: "\n".join([json.dumps({"type": "session_meta", "payload": {"cli_version": v}}),
                                      json.dumps({"type": "turn_context", "payload": {"model": m}})])
    (d / "rollout-1.jsonl").write_text(rollout("0.157.0", "gpt-6-sol"))
    assert pin_mismatch(tmp_path / "job", CODEX) is None
    (d / "rollout-1.jsonl").write_text(rollout("0.159.1", "gpt-6.1-sol"))
    assert "gpt-6.1-sol" in pin_mismatch(tmp_path / "job", CODEX)


def test_codex_rate_limits_reads_resets_at(tmp_path):
    import time as _t
    from skill_placebo.runner import codex_rate_limits

    d = tmp_path / "t" / "agent"
    d.mkdir(parents=True)
    now = _t.time()
    (d / "rollout-1.jsonl").write_text(json.dumps({"type": "event_msg", "payload": {"rate_limits": {
        "primary": {"used_percent": 24.0, "window_minutes": 300, "resets_at": now + 1800},
        "secondary": {"used_percent": 1.0, "window_minutes": 10080, "resets_at": now + 7 * 86400}}}}))
    rl = codex_rate_limits(tmp_path / "t")
    assert rl["five_hour"] == 24.0 and rl["weekly"] == 1.0
    assert 1790 < rl["five_hour_resets_s"] <= 1800 and rl["weekly_resets_at"] > now


def test_run_batch_waits_while_pause_file_exists(tmp_path, monkeypatch, capsys):
    from skill_placebo import runner

    monkeypatch.setattr(runner, "ROOT", tmp_path)
    monkeypatch.setattr(runner, "sweep_snapshots", lambda own=None: None)
    jobs = tmp_path / "jobs" / "b"
    jobs.mkdir(parents=True)
    (jobs / "PAUSE").write_text("test pause")
    sleeps = []

    def fake_sleep(s):  # the operator removes the file during the first wait
        sleeps.append(s)
        (jobs / "PAUSE").unlink(missing_ok=True)
    monkeypatch.setattr(runner.time, "sleep", fake_sleep)
    monkeypatch.setattr(runner, "host_free_gib", lambda path="/": 3.0)  # then stop before any trial
    trials = runner.plan(["t1"], [runner.Arm("baseline")], "test-h", n=1, seed=1)
    state = runner.run_batch(trials, runner.Harness("test-h", "a", "m"), {"baseline": runner.Arm("baseline")},
                             jobs, units_budget=1e9, concurrency=1, disk_stop_gib=6)
    out = capsys.readouterr().out
    assert "pause:" in out and "resume: PAUSE removed" in out and sleeps == [60]
    assert state.stopped.startswith("host disk")
