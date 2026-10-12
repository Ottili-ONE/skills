"""Tests for the CLI edge cases found in the EXPAND pass. Offline, deterministic."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ROBOTS = Path(ROOT, "scripts", "robots.py")
WRITER = Path(ROOT, "scripts", "warc_writer.py")


def run(argv, stdin=None):
    return subprocess.run([sys.executable, *argv], input=stdin,
                          capture_output=True, text=True)


def test_robots_status_404_no_path_no_stdin():
    """E7: --status 404 must exit 0 (may crawl) WITHOUT requiring --path or stdin.

    The old code read stdin first, so `--status 404` with no stdin fell into
    the empty-body branch and exited 1 (default-deny) -- the exact opposite
    of RFC 9309 §2.3.1.3.
    """
    p = run([str(ROBOTS), "--status", "404"])
    assert p.returncode == 0, p.stderr
    assert "status_decision=true" in p.stdout
    assert "may crawl" in p.stderr


def test_robots_status_503_no_path_no_stdin():
    """E8: --status 503 must exit 1 (default-deny) without --path or stdin."""
    p = run([str(ROBOTS), "--status", "503"])
    assert p.returncode == 1, p.stderr
    assert "status_decision=false" in p.stdout
    assert "default-deny" in p.stderr


def test_robots_status_500_is_default_deny():
    p = run([str(ROBOTS), "--status", "500"])
    assert p.returncode == 1
    assert "status_decision=false" in p.stdout


def test_robots_status_404_with_stdin_still_works():
    """--status takes precedence even when stdin carries a body."""
    p = run([str(ROBOTS), "--status", "404"], stdin="User-agent: *\nDisallow: /\n")
    assert p.returncode == 0, p.stderr
    assert "status_decision=true" in p.stdout


def test_robots_path_still_required_without_status():
    p = run([str(ROBOTS)])
    assert p.returncode == 2  # argparse usage error
    assert "--path" in p.stderr


def test_warc_validate_missing_file_fails_not_argparse():
    """A missing WARC must be a validation FAIL (rc=1), not a usage error (rc=2).

    The validator is part of the resume contract: a broken resume must be
    reported as a validation failure, not silently as "wrong arguments".
    """
    p = run([str(WRITER), "--validate", "/nonexistent/x.warc.gz"])
    assert p.returncode == 1, (p.returncode, p.stderr)
    assert "FAIL: WARC file not found" in p.stderr


def test_warc_validate_with_file_flag_missing_file():
    p = run([str(WRITER), "--validate", "--file", "/nonexistent/y.warc.gz"])
    assert p.returncode == 1
    assert "FAIL: WARC file not found" in p.stderr


def test_warc_validate_empty_file_fails():
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".warc.gz", delete=False) as fh:
        fh.write(b"")
        path = fh.name
    p = run([str(WRITER), "--validate", path])
    assert p.returncode == 1, p.stderr
    assert "no records" in p.stderr
