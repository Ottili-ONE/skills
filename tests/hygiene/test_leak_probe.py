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

# The truth-kit job whose database the end-to-end rung probes. The kit gives
# this job its own database with a non-superuser application role.
JOB = "SKL-W1-01"

# The output of a probe that saw exactly its own row, none of the other and
# could not write a row of the other tenant.
GOOD_OUTPUT = "t\na_sees_own\t1\na_sees_b\t0\nunset_sees_rows\t0\nwrite_leaks\t0\n"
# The output of a probe that saw the other tenant's row as well.
LEAKING_OUTPUT = "t\na_sees_own\t2\na_sees_b\t1\nunset_sees_rows\t2\nwrite_leaks\t1\n"
# The output of a probe that never ran: the markers are missing.
MISSING_OUTPUT = "t\n"


def run_harness(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(HARNESS), *args],
        capture_output=True,
        text=True,
        cwd=ROOT,
        check=False,
    )


def run_judge(path: Path) -> subprocess.CompletedProcess[str]:
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
    assert "did not report unset_sees_rows" in judged.stderr, judged.stderr


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


def test_the_probe_sql_reports_the_unset_tenant_measurement() -> None:
    """The probe must measure what a session without a tenant can see."""
    migration = SKILL / "references" / "examples" / "good_migration.sql"
    result = run_harness("--print-probe-sql", str(migration))
    assert result.returncode == 0, result.stdout + result.stderr
    assert "SELECT 'unset_sees_rows', count(*)" in result.stdout, result.stdout


def test_the_probe_sql_sets_only_the_canonical_tenant_guc() -> None:
    """One tenant GUC: the probe sets the name the platform sets."""
    migration = SKILL / "references" / "examples" / "good_migration.sql"
    result = run_harness("--print-probe-sql", str(migration))
    assert result.returncode == 0, result.stdout + result.stderr
    accepted = json.loads(GUC_NAMES.read_text(encoding="utf-8"))["accepted_names"]
    names = [entry["name"] if isinstance(entry, dict) else entry for entry in accepted]
    assert names == ["app.company_id"], names
    for name in names:
        assert f"set_config('{name}'" in result.stdout, (name, result.stdout)
    for legacy in ("app.current_company_id", "ottili.company_id", "app.current_tenant"):
        assert f"set_config('{legacy}'" not in result.stdout, (legacy, result.stdout)


def truth_kit_urls(job: str) -> tuple[str, str] | None:
    """Return the admin and app URL of the truth-kit database of the job.

    None when the truth kit is not installed on this host: the kit carries its
    own npm dependencies, and a missing kit is a missing prerequisite, not a
    reason to report a green probe that never ran.
    """
    kit = ROOT / "scripts" / "truth" / "db.mjs"
    if not kit.is_file():
        return None
    urls: list[str] = []
    for role in ("admin", "app"):
        result = subprocess.run(
            ["node", str(kit), "url", "--job", job, "--role", role],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return None
        urls.append(result.stdout.strip())
    return urls[0], urls[1]


def probe_migration(tmp_path: Path, name: str, protected: bool) -> Path:
    """Write a migration with its own table and return the path."""
    policy = ""
    if protected:
        policy = (
            f"CREATE POLICY {name}_tenant ON {name}\n"
            "    AS PERMISSIVE FOR SELECT TO web_app\n"
            "    USING (company_id = current_setting('app.company_id', true));\n"
            f"ALTER TABLE {name} ENABLE ROW LEVEL SECURITY;\n"
            f"ALTER TABLE {name} FORCE ROW LEVEL SECURITY;\n"
        )
    sql = (
        f"CREATE TABLE IF NOT EXISTS {name} (\n"
        "    id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),\n"
        "    company_id text NOT NULL,\n"
        "    body       text NOT NULL\n"
        ");\n"
        f"{policy}"
        f"GRANT SELECT, INSERT ON {name} TO web_app;\n"
    )
    path = tmp_path / f"{name}.sql"
    path.write_text(sql, encoding="utf-8")
    return path


def wide_check_migration(tmp_path: Path, name: str) -> Path:
    """Write a migration whose read path is closed and whose write path is open.

    The USING clause is the product standard, so every row of another company
    is invisible to the probe. The WITH CHECK clause is ``true``, so the
    database accepts a row that claims another company. The read probe
    cannot see this, because nothing is readable that should not be.
    """
    sql = (
        f"CREATE TABLE {name} (\n"
        "    id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),\n"
        "    company_id text NOT NULL,\n"
        "    body       text NOT NULL\n"
        ");\n"
        f"CREATE POLICY {name}_tenant ON {name}\n"
        "    AS PERMISSIVE FOR ALL TO web_app\n"
        "    USING (company_id = current_setting('app.company_id', true))\n"
        "    WITH CHECK (true);\n"
        f"ALTER TABLE {name} ENABLE ROW LEVEL SECURITY;\n"
        f"ALTER TABLE {name} FORCE ROW LEVEL SECURITY;\n"
        f"GRANT SELECT, INSERT ON {name} TO web_app;\n"
    )
    path = tmp_path / f"{name}.sql"
    path.write_text(sql, encoding="utf-8")
    return path


def psql(url: str, sql: str) -> subprocess.CompletedProcess[str]:
    """Run one statement against a database of the truth kit."""
    return subprocess.run(
        [
            "psql",
            url,
            "-q",
            "-t",
            "-A",
            "-v",
            "ON_ERROR_STOP=1",
            "-c",
            sql,
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def prepare_application_role(admin_url: str, app_url: str) -> None:
    """Create the role the migration grants to and make the login a member."""
    login_role = app_url.split("://", 1)[1].split(":", 1)[0].split("@", 1)[0]
    database = app_url.rsplit("/", 1)[1].split("?", 1)[0]
    created = psql(
        admin_url,
        "DO $$ BEGIN IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'web_app')"
        " THEN CREATE ROLE web_app NOLOGIN; END IF; END $$;",
    )
    assert created.returncode == 0, created.stdout + created.stderr
    granted = psql(
        admin_url,
        f'GRANT CONNECT ON DATABASE "{database}" TO web_app;'
        " GRANT USAGE ON SCHEMA public TO web_app;"
        f" GRANT web_app TO {login_role};",
    )
    assert granted.returncode == 0, granted.stdout + granted.stderr


def reachable(url: str) -> bool:
    """True when the database of the job answers.

    The truth kit hands out the URL of the database of the job, but the
    database itself is created by ``db.mjs create``. A host that has no
    PostgreSQL running has no database, and a test that claims a leak test
    green without a database would be a lie.
    """
    return psql(url, "SELECT 1;").returncode == 0


def test_the_probe_isolates_two_companies_on_a_real_postgres(tmp_path: Path) -> None:
    """The end-to-end rung: a real PostgreSQL, a non-superuser role, two companies.

    The application role is not the owner of the table and not a superuser,
    so row level security really decides what it sees.
    """
    migration = probe_migration(tmp_path, "rls_probe_protected", protected=True)
    urls = truth_kit_urls(JOB)
    if urls is None:
        result = run_harness("--server", "--job", JOB, str(migration), "rls_probe_protected")
        assert result.returncode == 2, result.stdout + result.stderr
        assert "no server" in result.stderr or "truth kit" in result.stderr, result.stderr
        return
    admin_url, app_url = urls
    result = run_harness(
        "--server",
        "--admin-url",
        admin_url,
        "--app-url",
        app_url,
        "--reset",
        str(migration),
        "rls_probe_protected",
    )
    if result.returncode == 2 and "not reachable" in result.stderr:
        # No PostgreSQL on this host: the harness has to refuse, and it has to
        # say that it refused. It must never report a green probe it did not
        # make.
        assert "PASS" not in result.stdout, result.stdout
        return
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS" in result.stdout, result.stdout
    assert "a_sees_own\t1" in result.stdout, result.stdout
    assert "a_sees_b\t0" in result.stdout, result.stdout
    assert "unset_sees_rows\t0" in result.stdout, result.stdout


def test_the_probe_catches_a_leak_on_a_real_postgres(tmp_path: Path) -> None:
    """A table without a policy leaks, and the probe has to say so."""
    migration = probe_migration(tmp_path, "rls_probe_leaking", protected=False)
    urls = truth_kit_urls(JOB)
    if urls is None:
        result = run_harness("--server", "--job", JOB, str(migration), "rls_probe_leaking")
        assert result.returncode == 2, result.stdout + result.stderr
        return
    admin_url, app_url = urls
    result = run_harness(
        "--server",
        "--admin-url",
        admin_url,
        "--app-url",
        app_url,
        "--reset",
        str(migration),
        "rls_probe_leaking",
    )
    if result.returncode == 2 and "not reachable" in result.stderr:
        assert "PASS" not in result.stdout, result.stdout
        return
    assert result.returncode == 1, result.stdout + result.stderr
    assert "cross-tenant leak" in result.stderr, result.stderr
    assert "rows visible without a tenant" in result.stderr, result.stderr


def test_the_write_path_of_a_policy_is_a_leak_the_probe_sees(
    tmp_path: Path,
) -> None:
    """The read path is closed, the write path is not, and both guards say so.

    A policy whose USING clause is the product standard hides every row of
    another company, so the probe of the read path measures 1, 0 and 0 and
    would report a green leak test. Its WITH CHECK clause is wide open, so the
    database writes a row that claims another company. The write measurement
    of the probe and the static gate both have to reject it.
    """
    checker = SKILL / "scripts" / "check_rls_migration.py"
    name = "rls_probe_wide_check"
    tenant_a = "11111111-1111-4111-8111-111111111111"
    tenant_b = "22222222-2222-4222-8222-222222222222"
    migration = wide_check_migration(tmp_path, name)

    urls = truth_kit_urls(JOB)
    if urls is None:
        result = run_harness("--server", "--job", JOB, str(migration), name)
        assert result.returncode == 2, result.stdout + result.stderr
        assert "PASS" not in result.stdout, result.stdout
        return
    admin_url, app_url = urls

    if not reachable(admin_url):
        result = run_harness(
            "--server",
            "--admin-url",
            admin_url,
            "--app-url",
            app_url,
            str(migration),
            name,
        )
        assert result.returncode == 2, result.stdout + result.stderr
        assert "PASS" not in result.stdout, result.stdout
        return

    prepare_application_role(admin_url, app_url)
    applied = psql(admin_url, migration.read_text(encoding="utf-8"))
    if applied.returncode != 0:
        # No PostgreSQL on this host: the harness has to refuse, and it has
        # to say that it refused. It must never report a green probe it did
        # not make.
        result = run_harness(
            "--server", "--admin-url", admin_url, "--app-url", app_url, str(migration), name
        )
        assert result.returncode == 2, result.stdout + result.stderr
        assert "PASS" not in result.stdout, result.stdout
        return
    try:
        # The read path of this migration is closed: the three read
        # measurements are right.
        probed = run_harness(
            "--server",
            "--admin-url",
            admin_url,
            "--app-url",
            app_url,
            "--reset",
            str(migration),
            name,
        )
        assert "a_sees_own\t1" in probed.stdout, probed.stdout
        assert "a_sees_b\t0" in probed.stdout, probed.stdout
        assert "unset_sees_rows\t0" in probed.stdout, probed.stdout
        # The write path is not closed, and the probe says so.
        assert "write_leaks\t1" in probed.stdout, probed.stdout
        assert probed.returncode == 1, probed.stdout + probed.stderr
        assert "write leak" in probed.stderr, probed.stderr

        # The write path of the same migration is open: the session of the
        # second company writes a row that claims the first company.
        written = psql(
            app_url,
            "BEGIN;"
            f"SELECT set_config('app.company_id', '{tenant_b}', true);"
            f"INSERT INTO {name} (company_id, body)"
            f" VALUES ('{tenant_a}', 'row of B claiming A');"
            "COMMIT;",
        )
        assert written.returncode == 0, written.stdout + written.stderr
        rows = psql(
            admin_url,
            f"SELECT count(*) FROM {name}"
            f" WHERE body = 'row of B claiming A' AND company_id = '{tenant_a}';",
        )
        assert rows.stdout.strip() == "1", rows.stdout
    finally:
        psql(admin_url, f'DROP TABLE IF EXISTS "{name}" CASCADE;')

    # The static gate rejects the migration as well.
    judged = subprocess.run(
        [shutil.which("python3") or "python3", str(checker), str(migration)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert judged.returncode == 1, judged.stdout + judged.stderr
    assert "write path of the policy is not constrained" in judged.stderr, judged.stderr


def test_the_canonical_example_can_be_applied_twice(tmp_path: Path) -> None:
    """The example the skill teaches must survive a second application.

    A migration that cannot be applied twice cannot be retried after a
    failed deployment, and a retry that aborts leaves the schema half
    migrated. The product migrations create their policies inside a DO block
    that asks pg_policies first; the example of the skill does the same, and
    this test holds it to it on a real PostgreSQL.
    """
    example = SKILL / "references" / "examples" / "good_migration.sql"
    urls = truth_kit_urls(JOB)
    if urls is None:
        result = run_harness("--server", "--job", JOB, str(example), "tenant_isolated_notes")
        assert result.returncode == 2, result.stdout + result.stderr
        assert "PASS" not in result.stdout, result.stdout
        return
    admin_url, app_url = urls
    if not reachable(admin_url):
        result = run_harness(
            "--server",
            "--admin-url",
            admin_url,
            "--app-url",
            app_url,
            str(example),
            "tenant_isolated_notes",
        )
        assert result.returncode == 2, result.stdout + result.stderr
        assert "PASS" not in result.stdout, result.stdout
        return
    prepare_application_role(admin_url, app_url)
    psql(admin_url, "DROP TABLE IF EXISTS tenant_isolated_notes CASCADE;")
    try:
        for attempt in (1, 2):
            applied = psql(admin_url, example.read_text(encoding="utf-8"))
            assert applied.returncode == 0, (
                f"application {attempt} failed: {applied.stdout}{applied.stderr}"
            )
        policies = psql(
            admin_url,
            "SELECT count(*) FROM pg_policies WHERE tablename = 'tenant_isolated_notes';",
        )
        assert policies.stdout.strip() == "2", policies.stdout
        # The example is still the good one after the second application.
        probed = run_harness(
            "--server",
            "--admin-url",
            admin_url,
            "--app-url",
            app_url,
            "--reset",
            str(example),
            "tenant_isolated_notes",
        )
        assert probed.returncode == 0, probed.stdout + probed.stderr
        assert "a_sees_own\t1" in probed.stdout, probed.stdout
        assert "a_sees_b\t0" in probed.stdout, probed.stdout
        assert "unset_sees_rows\t0" in probed.stdout, probed.stdout
    finally:
        psql(admin_url, "DROP TABLE IF EXISTS tenant_isolated_notes CASCADE;")
