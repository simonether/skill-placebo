import pytest

from skill_placebo import cli


def test_list_shows_the_nine_tested_skills(capsys):
    assert cli.main(["list"]) == 0
    out = capsys.readouterr().out.splitlines()
    assert len(out) == 9 and any("DietrichGebert/ponytail" in ln for ln in out)


def test_resolve_skill_by_repo_or_id():
    assert cli.resolve_skill(cli.HERE, "https://github.com/DietrichGebert/ponytail")["id"] == "ponytail"
    assert cli.resolve_skill(cli.HERE, "caveman")["repo"] == "JuliusBrussee/caveman"
    with pytest.raises(SystemExit):
        cli.resolve_skill(cli.HERE, "someone/unknown")


def test_run_dry_run_plans_three_arms_and_leaves_nothing(capsys):
    assert cli.main(["run", "DietrichGebert/ponytail", "--dry-run", "--tasks", "pandas-etl,largest-eigenval"]) == 0
    out = capsys.readouterr().out
    assert "12 trials (3 arms x 2 tasks x N=2)" in out and out.count("harbor_launch run") == 12
    assert not list((cli.HERE / "jobs" / "cli").glob("ponytail-*"))


def test_login_from_environment(monkeypatch):
    monkeypatch.delenv("CLAUDE_CODE_OAUTH_TOKEN", raising=False)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    h, creds = cli.claude_harness()
    assert h.creds == ("ANTHROPIC_API_KEY",) and "CLAUDE_FORCE_OAUTH" not in h.extra_env and creds["ANTHROPIC_API_KEY"] == "test-key"
