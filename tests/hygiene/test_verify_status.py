"""Regression tests for scripts/verify-status.mjs (SKL-W0-01).

``scripts/verify-status.mjs`` is the honest-status checker. It reads a
STATUS.md and fails every claim that is not backed by evidence.

Three defects made it useless, and all three are guarded here:

* it did not understand the format the product repositories write. Their
  STATUS.md files are claim tables — a row that asserts a success must name
  the command that was run, the exit code it returned and the log file that
  proves it. The checker read neither the rows nor their line numbers and
  answered "no false-done claims" for thousands of lines of prose;
* ``raw.rstrip()`` — a *Python* method — was called on a JavaScript string, so
  the checker died with ``TypeError: raw.rstrip is not a function``;
* ``require("node:fs")`` was called inside an ES module, where ``require`` is
  not defined. The resulting ``ReferenceError`` was swallowed by a bare
  ``catch``, so the log path was never checked and EVERY row was reported as
  "log path not found" — a checker that can never pass.

The real excerpts under ``tests/fixtures/status`` are verbatim copies of two
product repositories (provenance in ``tests/fixtures/PROVENANCE.md``); the
bad inputs are written inside the tests.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VERIFY_STATUS = ROOT / "scripts" / "verify-status.mjs"
NODE = shutil.which("node") or "node"
FIXTURES = ROOT / "tests" / "fixtures" / "status"

# A claim table in the format the product repositories write.
TABLE = """# Status

| Claim | Result | Evidence |
|---|---|---|
| {claim} | {result} | {evidence} |
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


def write_status(tmp_path: Path, claim: str, result: str, evidence: str) -> Path:
    """Write a STATUS.md with one claim row plus the log file it points at."""
    tree = tmp_path / "tree"
    (tree / "logs").mkdir(parents=True, exist_ok=True)
    status = tree / "STATUS.md"
    status.write_text(
        TABLE.format(claim=claim, result=result, evidence=evidence),
        encoding="utf-8",
    )
    return status


def test_the_real_status_excerpts_fail_with_line_numbers() -> None:
    """Two real product STATUS.md files must be reported, not waved through."""
    files = sorted(FIXTURES.glob("*.md"))
    assert len(files) == 2, f"expected 2 real STATUS excerpts as fixtures, found {files}"
    for path in files:
        result = run_checker(path, "--root", str(ROOT))
        assert result.returncode == 1, f"{path.name}: {result.stdout}{result.stderr}"
        assert "unverified row(s)" in result.stderr, result.stderr
        assert "line " in result.stderr, result.stderr


def test_a_real_status_excerpt_is_reported_as_json() -> None:
    """--json names the offending rows and their line numbers."""
    path = FIXTURES / "hq-v2-docs-STATUS.md"
    result = run_checker(path, "--root", str(ROOT), "--json")
    assert result.returncode == 1, result.stdout + result.stderr
    data = json.loads(result.stdout)
    assert data["status"] == "fail", data
    assert data["rows_checked"] > 0, data
    assert data["findings"], data
    first = data["findings"][0]
    assert first["line"] > 0, data
    assert first["problems"], data


def test_a_claim_with_an_existing_log_passes(tmp_path: Path) -> None:
    """A row whose evidence file exists is verified -> exit 0."""
    (tmp_path / "tree" / "logs").mkdir(parents=True, exist_ok=True)
    (tmp_path / "tree" / "logs" / "evidence.log").write_text("ran\n", encoding="utf-8")
    status = write_status(
        tmp_path,
        claim="`npm test`",
        result="**13 passed, 0 failed**, exit 0",
        evidence="`logs/evidence.log`",
    )

    result = run_checker(status, "--root", str(tmp_path / "tree"))
    assert result.returncode == 0, result.stdout + result.stderr
    assert "all 1 claim rows verified" in result.stdout, result.stdout


def test_a_claim_with_a_missing_log_fails(tmp_path: Path) -> None:
    """A row whose evidence file is missing is reported, not silently accepted."""
    status = write_status(
        tmp_path,
        claim="`npm test`",
        result="**13 passed, 0 failed**, exit 0",
        evidence="`logs/does-not-exist.log`",
    )

    result = run_checker(status, "--root", str(tmp_path / "tree"))
    assert result.returncode == 1, result.stdout + result.stderr
    assert "log path not found: logs/does-not-exist.log" in result.stderr, result.stderr
    assert "TypeError" not in result.stderr, result.stderr


def test_a_claim_without_a_log_path_fails(tmp_path: Path) -> None:
    """A row that names no evidence file at all is a finding."""
    status = write_status(
        tmp_path,
        claim="`npm test`",
        result="**13 passed, 0 failed**, exit 0",
        evidence="nothing to open",
    )

    result = run_checker(status, "--root", str(tmp_path / "tree"))
    assert result.returncode == 1, result.stdout + result.stderr
    assert "no log path" in result.stderr, result.stderr


def test_a_claim_without_an_exit_code_fails(tmp_path: Path) -> None:
    """"it passed" without an exit code is not a verified claim."""
    status = write_status(
        tmp_path,
        claim="`npm test`",
        result="**13 passed**",
        evidence="`logs/evidence.log`",
    )
    (tmp_path / "tree" / "logs" / "evidence.log").write_text("ran\n", encoding="utf-8")

    result = run_checker(status, "--root", str(tmp_path / "tree"))
    assert result.returncode == 1, result.stdout + result.stderr
    assert "no exit code" in result.stderr, result.stderr


def test_a_row_that_asserts_no_success_is_not_a_claim(tmp_path: Path) -> None:
    """A table of facts is not a set of claims; it must not produce findings."""
    status = write_status(
        tmp_path,
        claim="Node / npm",
        result="v24.19.0 / 11.17.0",
        evidence="`node -v`",
    )

    result = run_checker(status, "--root", str(tmp_path / "tree"))
    assert result.returncode == 0, result.stdout + result.stderr
    assert "all 0 claim rows verified" in result.stdout, result.stdout


def test_the_bucket_format_still_works(tmp_path: Path) -> None:
    """The grammar of the skill itself keeps working."""
    (tmp_path / "evidence.json").write_text("{}", encoding="utf-8")
    status = tmp_path / "STATUS.md"
    status.write_text(
        "## DONE\n- [x] the checker ships - evidence: evidence.json\n",
        encoding="utf-8",
    )

    result = run_checker(status, "--root", str(tmp_path))
    assert result.returncode == 0, result.stdout + result.stderr


def test_usage_error_when_no_file_is_given() -> None:
    """Without a file argument the checker exits 2 (usage error), not 0."""
    result = run_checker()
    assert result.returncode == 2, result.stdout + result.stderr
    assert "usage:" in result.stderr, result.stderr
