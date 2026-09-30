import os
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
