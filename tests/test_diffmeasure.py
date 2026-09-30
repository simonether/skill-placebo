import json

from skill_placebo.collect import edit_tool_lines
from skill_placebo.diffmeasure import base_commit, parse_docker_diff, parse_numstat, parse_wc


def test_parse_numstat_counts_text_and_binary():
    out = "3\t1\tdjango/a.py\n0\t2\tdjango/b.py\n-\t-\timg.png\n"
    assert parse_numstat(out) == {"tracked_added": 3, "tracked_deleted": 3, "tracked_files": 3, "tracked_binary": 1}


def test_parse_wc_skips_total():
    assert parse_wc("  31 solution_patch.diff\n   3 note.txt\n  34 total\n") == {"untracked_lines": 34, "untracked_files": 2}
    assert parse_wc("") == {"untracked_lines": 0, "untracked_files": 0}


def test_parse_docker_diff_ignores_install_noise():
    out = "C /app\nC /app/eigen.py\nA /tmp/x\nA /root/.local/bin/claude\nC /usr/lib/x\nD /app/old.py\n"
    r = parse_docker_diff(out)
    assert r["docker_diff"] == {"A": 0, "C": 2, "D": 1}


def test_base_commit_from_verifier_script(tmp_path):
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test.sh").write_text("git checkout " + "a" * 40 + " tests/x.py\n")
    assert base_commit(tmp_path) == "a" * 40
    assert base_commit(tmp_path / "missing") is None


def test_edit_tool_lines_counts_successful_calls_only(tmp_path):
    a = tmp_path / "agent"
    a.mkdir()
    use = lambda i, name, inp: {"type": "assistant", "message": {"content": [{"type": "tool_use", "id": i, "name": name, "input": inp}]}}
    res = lambda i, err: {"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": i, "is_error": err}]}}
    events = [use("1", "Edit", {"old_string": "a\nb", "new_string": "a\nb\nc"}), res("1", False),
              use("2", "Write", {"content": "x\ny\n"}), res("2", False),
              use("3", "Edit", {"old_string": "zzz", "new_string": "q"}), res("3", True),
              use("4", "Bash", {"command": "sed -i s/a/b/ f"}), res("4", False)]
    (a / "claude-code.txt").write_text("\n".join(json.dumps(e) for e in events))
    assert edit_tool_lines(tmp_path) == {"edit_calls": 2, "edit_lines_written": 5, "edit_lines_replaced": 2}
