"""Regression tests for the RLS leak-test harness (SKL-W0-01).

``skills/engineering/pg-rls-multitenant/scripts/pg-rls-leak-test.sh`` starts a
throwaway PostgreSQL, applies a migration under test, seeds two tenants and
probes the table AS the application role. It had two defects that made it
impossible to ever print PASS:

* the probe SQL printed the measurements as *aliased* columns
  (``SELECT count(*) AS a_sees_own``). ``psql -t -A`` prints tuples only and
  drops the alias, so the output was a bare ``1`` and a bare ``0``. The parser
  then looked for the label, found nothing, and the harness died under
  ``set -euo pipefail`` before it could print a verdict;
* the parser itself was a shell pipeline that treated "no match" as "no
  measurement", so a probe that never ran looked like a probe that measured
  zero.

The fix prints the label as a *value* (``SELECT 'a_sees_own', count(*)``) and
delegates the judgement to ``check_leak_probe.py``, which treats a missing
measurement as a failure rather than as a zero.

The Docker rung needs a Docker daemon, which this host does not have; the
committed tests therefore drive the two modes that need no daemon
(``--print-probe-sql`` and ``--parse``) and the end-to-end rung against real
PostgreSQL is recorded as UNVERIFIED in ``docs/gaps/SKL-W0-01.md`` with the
exact ``docker`` command.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "skills" / "engineering" / "pg-rls-multitenant"
HARNESS = SKILL / "scripts" / "pg-rls-leak-test.sh"
JUDGE = SKILL / "scripts" / "check_leak_probe.py"
GUC_NAMES = SKILL / "guc-names.json"

# The output of a probe that saw exactly its own row and none of the other.
GOOD_OUTPUT = "t\nt\na_sees_own\t1\na_sees_b\t0\n"
# The output of a probe that saw the other tenant's row as well.
LEAKING_OUTPUT = "t\nt\na_sees_own\t2\na_sees_b\t1\n"
# The output of a probe that never ran: the markers are missing.
MISSING_OUTPUT = "t\nt\n"


def run_harness(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", str(HARNESS), *args],
        capture_output=True,
        text=True,
        cwd=ROOT,
        check=False,
    )


def run_judge(path: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [shutil.which("python3") or "python3", str(JUDGE), str(path)],
        capture_output=True,
        text=True,
        check=False,
    )


def test_the_probe_sql_prints_labelled_measurements(tmp_path: Path) -> None:
    """The probe SQL must print LABEL<tab>VALUE, not an aliased column.

    This is the SQL defect: with ``psql -t -A`` an alias is not printed, so
    the label had to become a value.
    """
    migration = SKILL / "references" / "examples" / "good_migration.sql"
    result = run_harness("--print-probe-sql", str(migration))
    assert result.returncode == 0, result.stdout + result.stderr
    assert "SELECT 'a_sees_own', count(*)" in result.stdout, result.stdout
    assert "SELECT 'a_sees_b', count(*)" in result.stdout, result.stdout
    assert "AS a_sees_own" not in result.stdout, result.stdout


def test_the_probe_sql_sets_every_accepted_tenant_guc() -> None:
    """The tenant setting names are configuration, not a constant of the harness."""
    migration = SKILL / "references" / "examples" / "good_migration.sql"
    result = run_harness("--print-probe-sql", str(migration))
    assert result.returncode == 0, result.stdout + result.stderr
    accepted = json.loads(GUC_NAMES.read_text(encoding="utf-8"))["accepted_names"]
    names = [entry["name"] if isinstance(entry, dict) else entry for entry in accepted]
    assert names, "guc-names.json lists no accepted name"
    for name in names:
        assert f"set_config('{name}'" in result.stdout, (name, result.stdout)


def test_a_good_probe_output_passes(tmp_path: Path) -> None:
    """A probe that saw only its own row is a PASS."""
    output = tmp_path / "probe.out"
    output.write_text(GOOD_OUTPUT, encoding="utf-8")

    judged = run_judge(output)
    assert judged.returncode == 0, judged.stdout + judged.stderr
    assert "PASS" in judged.stdout, judged.stdout

    parsed = run_harness("--parse", str(output))
    assert parsed.returncode == 0, parsed.stdout + parsed.stderr
    assert "PASS" in parsed.stdout, parsed.stdout


def test_a_leaking_probe_output_fails(tmp_path: Path) -> None:
    """A probe that saw the other tenant's row is a FAIL."""
    output = tmp_path / "probe.out"
    output.write_text(LEAKING_OUTPUT, encoding="utf-8")

    judged = run_judge(output)
    assert judged.returncode == 1, judged.stdout + judged.stderr
    assert "cross-tenant leak" in judged.stderr, judged.stderr

    parsed = run_harness("--parse", str(output))
    assert parsed.returncode == 1, parsed.stdout + parsed.stderr
    assert "cross-tenant leak" in parsed.stderr, parsed.stderr


def test_a_probe_that_never_ran_fails(tmp_path: Path) -> None:
    """A missing measurement is a failure, not a zero."""
    output = tmp_path / "probe.out"
    output.write_text(MISSING_OUTPUT, encoding="utf-8")

    judged = run_judge(output)
    assert judged.returncode == 1, judged.stdout + judged.stderr
    assert "did not report a_sees_own" in judged.stderr, judged.stderr
    assert "did not report a_sees_b" in judged.stderr, judged.stderr


def test_a_probe_that_erred_fails(tmp_path: Path) -> None:
    """An error in the probe output is a failure, never a silent zero."""
    output = tmp_path / "probe.out"
    output.write_text(
        'psql:probe.sql:5: ERROR:  relation "tenant_isolated_notes" does not exist\n',
        encoding="utf-8",
    )

    judged = run_judge(output)
    assert judged.returncode == 1, judged.stdout + judged.stderr
    assert "probe error" in judged.stderr, judged.stderr


def test_the_harness_reports_a_usage_error() -> None:
    """A missing migration file is a usage error, not a silent pass."""
    result = run_harness()
    assert result.returncode == 2, result.stdout + result.stderr
