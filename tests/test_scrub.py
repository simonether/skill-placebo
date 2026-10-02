import os
import re
import subprocess
import sys
from pathlib import Path

SCRUB = Path(__file__).resolve().parents[1] / "scripts" / "scrub.py"


def test_non_utf8_file_is_still_checked_for_patterns(tmp_path):
    f = tmp_path / "history.patch"
    f.write_bytes(b"\xff\xfe stray bytes\n+cd " + os.path.expanduser("~").encode() + b"/projects/x\n")
    r = subprocess.run([sys.executable, str(SCRUB), "--check", str(f)], capture_output=True, text=True)
    assert r.returncode == 1 and "home-path" in r.stdout


def test_clean_non_utf8_file_passes(tmp_path):
    f = tmp_path / "blob.bin"
    f.write_bytes(b"\xff\xfe\x00 nothing sensitive here")
    r = subprocess.run([sys.executable, str(SCRUB), "--check", str(f)], capture_output=True, text=True)
    assert r.returncode == 0


def run(args, extra=None):
    env = {**os.environ, "SCRUB_EXTRA_PATTERNS": extra} if extra is not None else os.environ
    return subprocess.run([sys.executable, str(SCRUB), *args], capture_output=True, text=True, env=env)


def test_personal_pattern_from_the_environment_is_caught_and_redacted(tmp_path):
    f = tmp_path / "log.txt"
    f.write_text("author: Someone.Private@Example.org\n")
    assert run(["--check", str(f)], "").returncode == 0  # not in the code
    r = run(["--check", str(f)], "# comment\nsomeone\\.private@example\\.org")
    assert r.returncode == 1 and f"{f}:1: personal" in r.stdout and "Example.org" not in r.stdout
    run(["--redact", str(f)], "someone\\.private@example\\.org")
    assert f.read_text() == "author: [REDACTED:personal]\n"


def test_personal_pattern_is_checked_in_non_utf8_files(tmp_path):
    f = tmp_path / "history.patch"
    f.write_bytes(b"\xff\xfe stray bytes\n+From: someone.private@example.org\n")
    r = run(["--check", str(f)], "someone\\.private@example\\.org")
    assert r.returncode == 1 and "personal" in r.stdout


def test_no_e_mail_literals_in_the_code():
    assert not re.search(r"[\w.+-]+@[\w-]+\\?\.", SCRUB.read_text())
