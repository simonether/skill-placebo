import json

from skill_placebo.collect import cost_from_tokens, rows


def test_cost_from_tokens_sonnet():
    # 1M uncached-equivalent split: 100k uncached, 800k cache read, 100k cache write; 10k output
    c = cost_from_tokens("anthropic/claude-sonnet-5", 1_000_000, 800_000, 100_000, 10_000)
    assert abs(c - (100_000 * 2 + 800_000 * 0.2 + 100_000 * 2.5 + 10_000 * 10) / 1e6) < 1e-9
    assert cost_from_tokens("unknown-model", 1, 0, 0, 1) is None


def test_rows_parse_job_name_and_trial(tmp_path):
    job = tmp_path / "b00-0003__claude-code__placebo-t1__swebench-verified_django__django-10973"
    t = job / "django__django-10973__abc1234"
    (t / "agent").mkdir(parents=True)
    (t / "result.json").write_text(json.dumps({
        "task_name": "django__django-10973", "trial_name": "django__django-10973__abc1234",
        "agent_info": {"model_info": {"name": "claude-sonnet-5"}},
        "agent_result": {"n_input_tokens": 1000, "n_cache_tokens": 600, "n_output_tokens": 50, "cost_usd": 0.01},
        "verifier_result": {"rewards": {"reward": 1.0}},
    }))
    (t / "agent" / "trajectory.json").write_text(json.dumps({
        "final_metrics": {"extra": {"total_cache_creation_input_tokens": 100}},
        "steps": [{"tool_calls": [{"function_name": "Skill", "arguments": {"skill": "x"}}]}],
    }))
    (r,) = list(rows(tmp_path))
    assert r["harness"] == "claude-code" and r["arm"] == "placebo-t1"
    assert r["task"] == "swebench-verified_django__django-10973"
    assert r["passed"] == 1 and r["skill_fired"] == 1 and r["n_cache_write"] == 100


def test_retry_job_name_parsed(tmp_path):
    job = tmp_path / "b00-0001__claude-code__placebo-cc-3__say-ok__r1"
    t = job / "say-ok__xyz"
    (t / "agent").mkdir(parents=True)
    (t / "result.json").write_text(json.dumps({"task_name": "say-ok", "trial_name": "say-ok__xyz",
        "agent_info": {"model_info": {"name": "claude-opus-5-5"}}, "agent_result": {}, "verifier_result": {"rewards": {"reward": 1.0}}}))
    (r,) = list(rows(tmp_path))
    assert r["arm"] == "placebo-cc-3" and r["task"] == "say-ok" and r["attempt"] == 1 and r["infra_failure"] == 0


def test_verifier_timeout_is_a_failed_trial(tmp_path):
    job = tmp_path / "b00-0001__claude-code__placebo-cc-4__fix_async_worker_queue"
    t = job / "fix_async_worker_queue__x"
    (t / "agent").mkdir(parents=True)
    (t / "result.json").write_text(json.dumps({"task_name": "fix_async_worker_queue", "trial_name": "x",
        "agent_info": {"model_info": {"name": "claude-opus-5-5"}}, "agent_result": {"n_input_tokens": 10},
        "exception_info": {"exception_type": "VerifierTimeoutError"}}))
    (r,) = list(rows(tmp_path))
    assert r["passed"] == 0 and r["infra_failure"] == 0


def _timeout_trial(tmp_path):
    job = tmp_path / "b00-0001__claude-code__placebo-cc-4__fix_async_worker_queue"
    t = job / "fix_async_worker_queue__x"
    (t / "agent").mkdir(parents=True)
    (t / "result.json").write_text(json.dumps({"task_name": "fix_async_worker_queue", "trial_name": "x",
        "agent_info": {"model_info": {"name": "claude-opus-5-5"}}, "agent_result": {"n_input_tokens": 10},
        "exception_info": {"exception_type": "VerifierTimeoutError"}}))
    return t


def test_verifier_rerun_within_timeout_gives_the_reward(tmp_path):
    t = _timeout_trial(tmp_path)
    (t / "verifier_rerun.json").write_text(json.dumps({"outcome": "rerun within timeout", "reward": 1.0}))
    (r,) = list(rows(tmp_path))
    assert r["passed"] == 1 and r["reward"] == 1.0 and r["verifier_rerun"] == "rerun within timeout"
    assert r["infra_failure"] == 0  # the trial stays in the data; only the episode is flagged


def test_verifier_rerun_timeout_again_is_a_failed_trial(tmp_path):
    t = _timeout_trial(tmp_path)
    (t / "verifier_rerun.json").write_text(json.dumps({"outcome": "timeout again"}))
    (r,) = list(rows(tmp_path))
    assert r["passed"] == 0 and r["verifier_rerun"] == "timeout again"


def test_add_tests_dir_error_is_infrastructure(tmp_path):
    job = tmp_path / "b00-0106__claude-code__skill-karpathy__pandas-etl"
    t = job / "pandas-etl__x"
    (t / "agent").mkdir(parents=True)
    (t / "result.json").write_text(json.dumps({"task_name": "pandas-etl", "trial_name": "x",
        "agent_info": {"model_info": {"name": "claude-opus-5-5"}}, "agent_result": {},
        "exception_info": {"exception_type": "AddTestsDirError"}}))
    (r,) = list(rows(tmp_path))
    assert r["passed"] is None and r["infra_failure"] == 1
