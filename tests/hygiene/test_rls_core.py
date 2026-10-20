"""Unit tests of the typed core of the tenant checker (SKL-W1-01).

The core is the part of the checker that is pure: the data model, the reader
of the tenant convention, the SQL scanner, the rules and the judgement of a
leak probe. These tests drive it directly - no subprocess, no mock, no
database - and they read the real convention file of the skill.

The database is proven elsewhere: ``tests/hygiene/test_leak_probe.py`` runs
the probe against a real PostgreSQL with a non-superuser application role.
"""
from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "skills" / "engineering" / "pg-rls-multitenant"
SCRIPTS = SKILL / "scripts"
CONVENTION_FILE = SKILL / "guc-names.json"


def core() -> ModuleType:
    """Return the core package of the skill."""
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    return importlib.import_module("ottili_rls")


def convention() -> Any:
    """Return the tenant convention of the skill."""
    return core().load_convention(CONVENTION_FILE)


# ---------------------------------------------------------------------------
# The convention: one tenant GUC, one tenant column.
# ---------------------------------------------------------------------------


def test_the_convention_holds_exactly_one_tenant_guc() -> None:
    """``app.company_id`` is the one tenant GUC, ``company_id`` the column."""
    loaded = convention()
    assert loaded.accepted_names == ("app.company_id",), loaded.accepted_names
    assert loaded.canonical_name == "app.company_id", loaded.canonical_name
    assert loaded.canonical_column == "company_id", loaded.canonical_column


def test_a_configuration_with_two_tenant_gucs_is_refused(tmp_path: Path) -> None:
    """A configuration that is not one convention must not be half applied."""
    path = tmp_path / "guc-names.json"
    path.write_text(
        json.dumps(
            {
                "canonical_name": "app.company_id",
                "accepted_names": [
                    {"name": "app.company_id"},
                    {"name": "ottili.company_id"},
                ],
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(core().ConventionError):
        core().load_convention(path)


def test_a_missing_convention_file_is_refused(tmp_path: Path) -> None:
    """Without the convention the checker cannot judge; it must not guess."""
    with pytest.raises(core().ConventionError):
        core().load_convention(tmp_path / "does-not-exist.json")


def test_a_broken_convention_file_is_refused(tmp_path: Path) -> None:
    """A file that is not JSON is an error, not an empty convention."""
    path = tmp_path / "guc-names.json"
    path.write_text("{not json", encoding="utf-8")
    with pytest.raises(core().ConventionError):
        core().load_convention(path)


def test_classify_guc_knows_the_four_answers() -> None:
    """Canonical, rejected, not-a-tenant and unknown are four different things."""
    loaded = convention()
    classify = core().classify_guc
    assert classify("app.company_id", loaded) is core().GucStatus.CANONICAL
    assert classify("ottili.company_id", loaded) is core().GucStatus.REJECTED
    assert classify("app.current_tenant", loaded) is core().GucStatus.REJECTED
    assert classify("app.is_superadmin", loaded) is core().GucStatus.NON_TENANT
    assert classify("app.not_a_real_setting", loaded) is core().GucStatus.UNKNOWN
    assert classify("", loaded) is core().GucStatus.UNKNOWN


# ---------------------------------------------------------------------------
# The scanner: what a migration says.
# ---------------------------------------------------------------------------


def test_a_semicolon_inside_a_literal_does_not_end_a_statement() -> None:
    """A literal is data, not a statement boundary."""
    statements = core().split_statements(
        "INSERT INTO notes (body) VALUES ('a;b');\nSELECT 1;\n"
    )
    assert len(statements) == 2, statements


def test_a_comment_is_prose_and_not_a_statement() -> None:
    """A commented-out statement is not a statement."""
    statements = core().split_statements("-- DROP TABLE notes;\nSELECT 1;\n")
    assert len(statements) == 1, statements
    assert "DROP TABLE" not in statements[0], statements
    assert "SELECT 1" in statements[0], statements


def test_the_scanner_reads_a_do_block() -> None:
    """A policy inside ``DO $$ ... $$`` is a policy."""
    sql = """\
CREATE TABLE notes (id uuid PRIMARY KEY, company_id text NOT NULL);
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'notes') THEN
    ALTER TABLE notes ENABLE ROW LEVEL SECURITY;
    ALTER TABLE notes FORCE ROW LEVEL SECURITY;
  END IF;
END
$$;
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'notes') THEN
    CREATE POLICY notes_tenant ON notes USING (company_id = current_setting('app.company_id', true));
  END IF;
END
$$;
"""
    facts = core().collect_facts(core().split_statements(sql))
    table = facts.table("notes")
    assert table is not None, facts
    assert table.enabled_rls, table
    assert table.forced_rls, table
    assert table.policies, table


def test_the_scanner_reads_the_doubled_quote_spelling() -> None:
    """A policy created with EXECUTE writes the setting with doubled quotes."""
    sql = """\
CREATE TABLE notes (id uuid PRIMARY KEY, company_id text NOT NULL);
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'notes') THEN
    EXECUTE 'CREATE POLICY notes_tenant ON notes USING (company_id = current_setting(''app.company_id'', true))';
  END IF;
END
$$;
"""
    facts = core().collect_facts(core().split_statements(sql))
    table = facts.table("notes")
    assert table is not None, facts
    assert table.policies, table
    assert core().canonical_gucs_used(facts, convention()) == {"app.company_id"}


def test_a_composite_key_stays_one_column_definition() -> None:
    """``PRIMARY KEY (company_id, id)`` is one definition, not two columns."""
    parts = core().split_column_definitions(
        "id uuid PRIMARY KEY, company_id text NOT NULL, PRIMARY KEY (company_id, id)"
    )
    assert len(parts) == 3, parts


# ---------------------------------------------------------------------------
# The rules: what a migration gets wrong.
# ---------------------------------------------------------------------------

GOOD_MIGRATION = """\
CREATE TABLE notes (
    id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id text        NOT NULL,
    body       text        NOT NULL
);
CREATE POLICY notes_tenant ON notes
    FOR SELECT TO web_app
    USING (company_id = current_setting('app.company_id', true));
ALTER TABLE notes ENABLE ROW LEVEL SECURITY;
ALTER TABLE notes FORCE ROW LEVEL SECURITY;
"""


def test_a_good_migration_has_no_findings() -> None:
    """The product standard is a clean migration."""
    assert core().evaluate_migration(GOOD_MIGRATION, convention()) == []


def test_every_rule_has_its_own_finding() -> None:
    """A migration that breaks every rule reports every rule."""
    sql = """\
CREATE TABLE notes (
    id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id text,
    body       text        NOT NULL
);
CREATE POLICY notes_tenant ON notes
    FOR SELECT TO web_app
    USING (company_id = current_setting('ottili.company_id', true));
ALTER TABLE notes ENABLE ROW LEVEL SECURITY;
GRANT ALL ON notes TO web_app;
"""
    findings = core().evaluate_migration(sql, convention())
    codes = {finding.code for finding in findings}
    assert core().FindingCode.NULLABLE_COMPANY_ID in codes, findings
    assert core().FindingCode.MISSING_FORCE_RLS in codes, findings
    assert core().FindingCode.NON_CANONICAL_GUC in codes, findings
    assert core().FindingCode.GRANT_ALL in codes, findings


def test_a_table_without_the_tenant_column_is_a_finding() -> None:
    """A tenant table without the discriminator column is not tenant-safe."""
    sql = GOOD_MIGRATION.replace("company_id text        NOT NULL", "tenant_id text NOT NULL")
    codes = {f.code for f in core().evaluate_migration(sql, convention())}
    assert core().FindingCode.MISSING_COMPANY_ID in codes, codes


def test_a_policy_without_a_tenant_setting_is_a_finding() -> None:
    """A policy that reads no tenant setting isolates nobody."""
    sql = GOOD_MIGRATION.replace(
        "current_setting('app.company_id', true)", "true"
    )
    codes = {f.code for f in core().evaluate_migration(sql, convention())}
    assert core().FindingCode.UNKNOWN_GUC in codes, codes


def test_the_findings_are_deterministic() -> None:
    """The same input and the same convention produce the same findings."""
    sql = GOOD_MIGRATION.replace("company_id text        NOT NULL", "company_id text")
    first = core().evaluate_migration(sql, convention())
    second = core().evaluate_migration(sql, convention())
    assert first == second, (first, second)


def test_a_finding_renders_with_its_table() -> None:
    """The text of a finding names the table it belongs to."""
    finding = core().Finding(
        code=core().FindingCode.MISSING_ENABLE_RLS,
        message="missing ENABLE ROW LEVEL SECURITY",
        table="notes",
    )
    assert finding.render() == "notes: missing ENABLE ROW LEVEL SECURITY"


# ---------------------------------------------------------------------------
# The judgement of a leak probe.
# ---------------------------------------------------------------------------


def test_the_judgement_needs_every_measurement() -> None:
    """A missing measurement is a failure, not a zero."""
    verdict = core().judge_probe_output("a_sees_own\t1\na_sees_b\t0\n")
    assert not verdict.passed, verdict
    assert any("unset_sees_rows" in finding for finding in verdict.findings), (
        verdict.findings
    )


def test_the_judgement_names_the_leak() -> None:
    """A cross-tenant leak is named, not summarised."""
    verdict = core().judge_probe_output(
        "a_sees_own\t2\na_sees_b\t1\nunset_sees_rows\t2\n"
    )
    assert not verdict.passed, verdict
    assert any("cross-tenant leak" in f for f in verdict.findings), verdict.findings
    assert any("without a tenant" in f for f in verdict.findings), verdict.findings


def test_a_clean_probe_output_passes() -> None:
    """The three measurements of a clean probe: one own row, nothing else."""
    verdict = core().judge_probe_output(
        "a_sees_own\t1\na_sees_b\t0\nunset_sees_rows\t0\n"
    )
    assert verdict.passed, verdict.findings
    assert len(verdict.measurements) == 3, verdict.measurements


# ---------------------------------------------------------------------------
# The run log.
# ---------------------------------------------------------------------------


def test_the_run_log_is_one_json_object(capsys: pytest.CaptureFixture[str]) -> None:
    """A log line is machine-readable and carries the run id."""
    import logging

    logger = core().configure_logging("INFO")
    logger.handlers.clear()
    core().configure_logging("INFO")
    run_id = core().new_run_id()
    core().log_event(logger, logging.INFO, "migration checked", run_id, file="notes.sql")
    payload = json.loads(capsys.readouterr().err.strip())
    assert payload["run_id"] == run_id, payload
    assert payload["message"] == "migration checked", payload
    assert payload["file"] == "notes.sql", payload
    assert payload["level"] == "info", payload
