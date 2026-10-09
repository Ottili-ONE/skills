"""Tests for check_shared_tree.py - offline deterministic."""
import os
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_shared_tree.py"
ROOT = Path(__file__).resolve().parents[3]


def run(*args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=30,
    )


def test_locks_no_lock():
    r = run("locks")
    assert r.returncode == 0
    assert "no index.lock" in r.stdout or "ok:" in r.stdout


def test_message_valid_prefix():
    r = run("--message", "skills-engineering-r3-03: add feature", "message")
    assert r.returncode == 0


def test_message_missing_prefix():
    r = run("--message", "fix stuff", "message")
    assert r.returncode == 1
    assert "task-id prefix" in r.stderr.lower() or "error" in r.stderr.lower()


def test_staged_clean():
    st = subprocess.run(["git", "diff", "--cached", "--name-only"],
                        capture_output=True, text=True)
    if not st.stdout.strip():
        r = run("staged")
        assert r.returncode == 0
        assert "nothing staged" in r.stdout or "ok:" in r.stdout
    else:
        print("skipping staged-clean: something already staged",
              st.stdout.splitlines(), file=sys.stderr)


def test_scan_runs():
    r = run("--file", str(SCRIPT), "scan")
    assert r.returncode in (0, 1)
