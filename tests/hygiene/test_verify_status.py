"""Regression tests for scripts/verify-status.mjs (SKL-W0-01).

``scripts/verify-status.mjs`` is the honest-status checker: it reads a
``STATUS.md`` claim table and fails a row whose command produced no evidence
file. Two defects made the checker unusable, and both are guarded here:

* ``raw.rstrip()`` — a *Python* method — was called on a JavaScript string, so
  the checker died with ``TypeError: raw.rstrip is not a function`` on the
  first table row it saw.
* ``require("node:fs")`` was called inside an ES module, where ``require`` is
  not defined. The resulting ``ReferenceError`` was swallowed by a bare
  ``catch``, so the log path was never checked and EVERY row was reported as
  "log path not found" — a checker that can never pass.

The tests below build a throwaway fixture tree under ``tmp_path``; they never
write into the repository.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VERIFY_STATUS = ROOT / "scripts" / "verify-status.mjs"
NODE = shutil.which("node") or "node"

TABLE = """# Status

| claim | command | result |
|---|---|---|
| {claim} | `{command}` | {result} |
"""


def run_checker(status_file: Path | None = None, *args: str) -> subprocess.CompletedProcess[str]:
    """Run verify-status.mjs against ``status_file``."""
    argv = [NODE, str(VERIFY_STATUS)]
    if status_file is not None:
        argv.append(str(status_file))
    return subprocess.run(
        [*argv, *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def make_tree(tmp_path: Path, claim: str, command: str, result: str) -> Path:
    """Write a STATUS.md with one claim row plus the log file it points at."""
    tree = tmp_path / "tree"
    (tree / "logs").mkdir(parents=True)
    status = tree / "STATUS.md"
    status.write_text(
        TABLE.format(claim=claim, command=command, result=result),
        encoding="utf-8",
    )
    return status


def test_a_claim_with_an_existing_log_passes(tmp_path: Path) -> None:
    """A row whose evidence file exists is verified -> exit 0.

    This is the case that crashed before the fix and that the swallowed
    ``require`` made impossible to pass.
    """
    tree = tmp_path / "tree"
    (tree / "logs").mkdir(parents=True)
    (tree / "logs" / "evidence.log").write_text("ran\n", encoding="utf-8")
    status = tree / "STATUS.md"
    status.write_text(
        TABLE.format(
            claim="the installer installs every skill",
            command="bash scripts/install.sh --package engineering",
            result="0 logs/evidence.log",
        ),
        encoding="utf-8",
    )

    result = run_checker(status, "--root", str(tree))
    assert result.returncode == 0, result.stdout + result.stderr
    assert "all 1 claim rows verified" in result.stdout, result.stdout


def test_a_claim_with_a_missing_log_fails(tmp_path: Path) -> None:
    """A row whose evidence file is missing is reported, not silently accepted."""
    status = make_tree(
        tmp_path,
        claim="the installer installs every skill",
        command="bash scripts/install.sh --package engineering",
        result="0 logs/does-not-exist.log",
    )

    result = run_checker(status, "--root", str(tmp_path / "tree"))
    assert result.returncode == 1, result.stdout + result.stderr
    assert "log path not found: logs/does-not-exist.log" in result.stderr, result.stderr
    assert "TypeError" not in result.stderr, result.stderr


def test_a_row_without_a_log_path_is_reported(tmp_path: Path) -> None:
    """A row that names no evidence file at all is a finding."""
    status = make_tree(
        tmp_path,
        claim="the build is green",
        command="make build",
        result="0",
    )

    result = run_checker(status, "--root", str(tmp_path / "tree"))
    assert result.returncode == 1, result.stdout + result.stderr
    assert "no log path" in result.stderr, result.stderr
    assert "TypeError" not in result.stderr, result.stderr


def test_json_output_reports_the_finding(tmp_path: Path) -> None:
    """--json lists the offending row and its line number."""
    status = make_tree(
        tmp_path,
        claim="the installer installs every skill",
        command="bash scripts/install.sh --package engineering",
        result="0 logs/does-not-exist.log",
    )

    result = run_checker(status, "--root", str(tmp_path / "tree"), "--json")
    assert result.returncode == 1, result.stdout + result.stderr
    assert '"status": "fail"' in result.stdout, result.stdout
    assert '"log path not found: logs/does-not-exist.log"' in result.stdout, result.stdout


def test_usage_error_when_no_file_is_given() -> None:
    """Without a file argument the checker exits 2 (usage error), not 0."""
    result = run_checker()
    assert result.returncode == 2, result.stdout + result.stderr
    assert "usage:" in result.stderr, result.stderr
