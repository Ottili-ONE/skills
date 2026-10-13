"""Tests for check_shared_tree.py - offline deterministic."""
import os
import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_shared_tree.py"
ROOT = Path(__file__).resolve().parents[3]


def run(*args, cwd=None):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=str(cwd or ROOT),
        capture_output=True,
        text=True,
        timeout=30,
    )


def test_locks_no_lock():
    r = run("locks")
    assert r.returncode == 0
    assert "no index.lock" in r.stdout or "ok:" in r.stdout


def test_locks_stale_binary_pid_removed():
    """A real index.lock is a 4-byte big-endian PID, not text."""
    tmp = Path(tempfile.mkdtemp())
    try:
        (tmp / ".git").mkdir()
        (tmp / ".git" / "index.lock").write_bytes(struct.pack(">i", 99999))
        # Default mode warns only; --force removes a lock whose PID is dead.
        r = run("--cwd", str(tmp), "--force", "locks")
        assert r.returncode == 0, r.stderr
        assert "stale" in r.stdout
        assert not (tmp / ".git" / "index.lock").exists()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_locks_live_pid_rejected():
    """A live PID in index.lock must NOT be auto-removed."""
    tmp = Path(tempfile.mkdtemp())
    try:
        (tmp / ".git").mkdir()
        (tmp / ".git" / "index.lock").write_bytes(struct.pack(">i", os.getpid()))
        r = run("--cwd", str(tmp), "locks")
        assert r.returncode == 1, r.stderr
        assert "live PID" in r.stderr
        assert (tmp / ".git" / "index.lock").exists()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


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


def test_scan_flags_forbidden():
    tmp = Path(tempfile.mkdtemp())
    try:
        (tmp / "bad.sh").write_text("#!/bin/sh\ngit reset --hard HEAD~1\n")
        r = run("--file", str(tmp / "bad.sh"), "scan")
        assert r.returncode == 1
        assert "reset --hard" in r.stderr
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    failed = 0
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"ok   {name}")
            except AssertionError as exc:
                print(f"FAIL {name}: {exc}")
                failed += 1
    if failed:
        print(f"{failed} test(s) failed")
        sys.exit(1)
    print("check_shared_tree self-test: PASS")
