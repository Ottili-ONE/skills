"""Guards for the tenant RLS checker (SKL-W0-01).

The checker lives in the skill ``pg-rls-multitenant``:
``skills/engineering/pg-rls-multitenant/scripts/check_rls_migration.py``.

Two defects made it useless and both are guarded here:

* the accepted tenant GUC name was a constant of the script, so every migration
  of a repository that uses another name (``ottili.company_id`` in the apps,
  ``app.current_company_id`` in ld3) was rejected, and the real corpus failed
  74 of 120 files for reasons that had nothing to do with the migration;
* the checker demanded ``CREATE TABLE`` in every file, so 70 real migrations
  that only touch an existing table were rejected as "not a tenant migration".

The fixtures under ``tests/fixtures/hq-migrations`` are verbatim copies of real
hq-v2 migrations (see ``tests/fixtures/PROVENANCE.md``). The hostile inputs are
written inside the tests: a test must never pass because a bad file changed.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CHECKER = ROOT / "skills" / "engineering" / "pg-rls-multitenant" / "scripts" / "check_rls_migration.py"
GUC_FILE = ROOT / "skills" / "engineering" / "pg-rls-multitenant" / "guc-names.json"
FIXTURES = ROOT / "tests" / "fixtures" / "hq-migrations"
SHAPES = ROOT / "tests" / "fixtures" / "rls-shapes"

TEMPLATE = """\
CREATE TABLE {table} (
    id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id text        NOT NULL,
    body       text        NOT NULL
);

CREATE POLICY {table}_tenant ON {table}
    FOR SELECT TO web_app
    USING (company_id = current_setting('{guc}', true));

ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;
ALTER TABLE {table} FORCE ROW LEVEL SECURITY;
"""


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CHECKER), *args], capture_output=True, text=True, check=False
    )


def write(tmp_path: Path, name: str, sql: str) -> Path:
    path = tmp_path / name
    path.write_text(sql, encoding="utf-8")
    return path


def test_the_three_real_hq_migrations_pass() -> None:
    """Three real hq-v2 migrations must pass the checker."""
    files = sorted(FIXTURES.glob("*.sql"))
    assert len(files) == 3, f"expected 3 real migrations as fixtures, found {files}"
    for path in files:
        result = run(str(path))
        assert result.returncode == 0, f"{path.name}: {result.stdout}{result.stderr}"


def test_a_hostile_migration_is_rejected(tmp_path: Path) -> None:
    """No FORCE: the owner of the table could still read every row."""
    sql = TEMPLATE.format(table="hostile_no_force", guc="app.company_id")
    sql = sql.replace("ALTER TABLE hostile_no_force FORCE ROW LEVEL SECURITY;\n", "")
    path = write(tmp_path, "no_force.sql", sql)
    result = run(str(path))
    assert result.returncode == 1, result.stdout + result.stderr
    assert "missing FORCE ROW LEVEL SECURITY" in result.stderr, result.stderr


def test_a_migration_without_company_id_is_rejected(tmp_path: Path) -> None:
    """A tenant table without the discriminator column is not tenant-safe."""
    sql = TEMPLATE.format(table="hostile_no_company", guc="app.company_id")
    sql = sql.replace("    company_id text        NOT NULL,\n", "    tenant_id  text        NOT NULL,\n")
    sql = sql.replace("company_id = current_setting", "tenant_id = current_setting")
    path = write(tmp_path, "no_company_id.sql", sql)
    result = run(str(path))
    assert result.returncode == 1, result.stdout + result.stderr
    assert "no company_id tenant discriminator column" in result.stderr, result.stderr


def test_grant_all_is_rejected(tmp_path: Path) -> None:
    """GRANT ALL overrides the policy the migration just wrote."""
    sql = TEMPLATE.format(table="hostile_grant", guc="app.company_id")
    sql += "\nGRANT ALL ON hostile_grant TO web_app;\n"
    path = write(tmp_path, "grant_all.sql", sql)
    result = run(str(path))
    assert result.returncode == 1, result.stdout + result.stderr
    assert "GRANT ALL" in result.stderr, result.stderr


def test_a_policy_on_an_unknown_guc_is_rejected(tmp_path: Path) -> None:
    """A setting name nobody sets isolates nobody: it must be a finding."""
    sql = TEMPLATE.format(table="unknown_guc", guc="app.not_a_real_setting")
    path = write(tmp_path, "unknown_guc.sql", sql)
    result = run(str(path))
    assert result.returncode == 1, result.stdout + result.stderr
    assert "not keyed on an accepted tenant GUC" in result.stderr, result.stderr


def test_every_accepted_guc_name_is_honoured(tmp_path: Path) -> None:
    """Every name in guc-names.json is accepted — the list is configuration."""
    config = json.loads(GUC_FILE.read_text(encoding="utf-8"))
    names = [entry["name"] for entry in config["accepted_names"]]
    assert names, "guc-names.json must list at least one accepted name"
    for name in names:
        sql = TEMPLATE.format(table=f"tenant_{name.replace('.', '_')}", guc=name)
        path = write(tmp_path, f"{name}.sql", sql)
        result = run(str(path))
        assert result.returncode == 0, f"{name}: {result.stdout}{result.stderr}"


def test_the_configuration_decides_which_names_pass(tmp_path: Path) -> None:
    """The checker must read its configuration, not hard-code a name."""
    config = tmp_path / "guc-names.json"
    config.write_text(
        json.dumps({"accepted_names": [{"name": "app.company_id"}]}), encoding="utf-8"
    )
    sql = TEMPLATE.format(table="other_guc", guc="ottili.company_id")
    path = write(tmp_path, "other_guc.sql", sql)
    result = run(str(path), "--guc-names", str(config))
    assert result.returncode == 1, result.stdout + result.stderr
    assert "not keyed on an accepted tenant GUC" in result.stderr, result.stderr


def test_a_missing_configuration_is_a_usage_error(tmp_path: Path) -> None:
    """Without the configuration the checker cannot judge; it must not guess."""
    sql = TEMPLATE.format(table="tenant_notes", guc="app.company_id")
    path = write(tmp_path, "ok.sql", sql)
    result = run(str(path), "--guc-names", str(tmp_path / "nope.json"))
    assert result.returncode == 2, result.stdout + result.stderr
    assert "cannot read the accepted tenant GUC names" in result.stderr, result.stderr


def test_a_migration_without_a_table_is_not_a_finding(tmp_path: Path) -> None:
    """A migration that only adds a column is not a tenant-table migration."""
    sql = "ALTER TABLE operations_follow_up ADD COLUMN created_via text;\n"
    path = write(tmp_path, "add_column.sql", sql)
    result = run(str(path))
    assert result.returncode == 0, result.stdout + result.stderr


# ---------------------------------------------------------------------------
# The two shapes the product repositories write and the checker used to
# misread. Both fixtures are verbatim copies of real migrations (provenance in
# tests/fixtures/PROVENANCE.md).
# ---------------------------------------------------------------------------


def test_a_do_block_migration_passes() -> None:
    """A real hq-v2 migration that sets RLS inside a ``DO $$ ... $$`` block.

    The checker read the body of a dollar-quoted block with a back-reference
    to a group that did not take part in the match. Such a back-reference
    never succeeds, so the untagged spelling - the one every ``DO`` block of
    the product repositories uses - was invisible: the checker reported
    "missing ENABLE ROW LEVEL SECURITY", "missing FORCE ROW LEVEL SECURITY"
    and "no CREATE POLICY" on a migration that does all three.
    """
    path = SHAPES / "hq-accounting-gl-do-block.sql"
    result = run(str(path))
    assert result.returncode == 0, result.stdout + result.stderr


def test_a_policy_created_with_execute_passes() -> None:
    """A real ottili-apps migration that creates its policy with ``EXECUTE``.

    The policy is a string literal, so the setting name is written with
    doubled quotes (``current_setting(''ottili.company_id'', true)``). The
    checker has to read that spelling, otherwise it rejects a policy that
    keys on an accepted tenant setting.
    """
    path = SHAPES / "ottili-apps-github-issue-link.sql"
    result = run(str(path))
    assert result.returncode == 0, result.stdout + result.stderr


def test_a_do_block_without_force_is_rejected(tmp_path: Path) -> None:
    """Reading a ``DO`` block must not make the checker blind inside it."""
    sql = """\
CREATE TABLE do_block_notes (
    id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id text NOT NULL,
    body       text NOT NULL
);

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'do_block_notes') THEN
    ALTER TABLE do_block_notes ENABLE ROW LEVEL SECURITY;
  END IF;
END
$$;

CREATE POLICY do_block_notes_tenant ON do_block_notes
    FOR SELECT TO web_app
    USING (company_id = current_setting('app.company_id', true));
"""
    path = write(tmp_path, "do_block_no_force.sql", sql)
    result = run(str(path))
    assert result.returncode == 1, result.stdout + result.stderr
    assert "missing FORCE ROW LEVEL SECURITY" in result.stderr, result.stderr


def test_a_policy_created_with_execute_on_an_unknown_setting_is_rejected(
    tmp_path: Path,
) -> None:
    """The escaped spelling must be read as strictly as the plain one."""
    sql = """\
CREATE TABLE execute_notes (
    id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id text NOT NULL,
    body       text NOT NULL
);

ALTER TABLE execute_notes ENABLE ROW LEVEL SECURITY;
ALTER TABLE execute_notes FORCE ROW LEVEL SECURITY;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'execute_notes') THEN
    EXECUTE
      'CREATE POLICY execute_notes_tenant ON execute_notes AS PERMISSIVE FOR ALL
         USING (company_id = NULLIF(current_setting(''app.not_a_real_setting'', true), ''''))';
  END IF;
END
$$;
"""
    path = write(tmp_path, "execute_unknown_guc.sql", sql)
    result = run(str(path))
    assert result.returncode == 1, result.stdout + result.stderr
    assert "not keyed on an accepted tenant GUC" in result.stderr, result.stderr
