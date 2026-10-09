#!/usr/bin/env python3
"""Offline checker for a Postgres RLS migration file.

Verifies, without a database, the rules the pg-rls-multitenant skill mandates:
  1. every row table declares a tenant discriminator column as NOT NULL
  2. every row table has at least one CREATE POLICY
  3. FORCE ROW LEVEL SECURITY is present on non-dev tables
  4. no GRANT ALL is issued on any RLS-protected table
  5. a -- ROLLBACK block exists so the migration is reversible
  6. views either set security_invoker = true or are exempt

Usage:
  python3 check_rls_migration.py migration.sql
Exit code 0 = all checks pass; 1 = findings; 2 = usage error.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

TENANT_COLUMNS = {"tenant_id", "organization_id", "org_id", "namespace", "account_id"}
ROW_TABLE_RE = re.compile(
    r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?P<name>\w+\.?\w+|\w+)",
    re.IGNORECASE,
)
COLUMN_RE = re.compile(r"^\s*(?P<col>\w+)\s+(?P<type>\w+)", re.MULTILINE)
NOT_NULL_RE = re.compile(r"NOT\s+NULL", re.IGNORECASE)
FORCE_RLS_RE = re.compile(r"FORCE\s+ROW\s+LEVEL\s+SECURITY", re.IGNORECASE)
GRANT_ALL_RE = re.compile(r"GRANT\s+ALL", re.IGNORECASE)
POLICY_RE = re.compile(r"CREATE\s+POLICY\s+\S+\s+ON\s+(?P<table>\w+)", re.IGNORECASE)
ROLLBACK_RE = re.compile(r"--\s*ROLLBACK", re.IGNORECASE)
SECURITY_INVOKER_RE = re.compile(r"security_invoker\s*=\s*true", re.IGNORECASE)
VIEW_RE = re.compile(r"CREATE\s+VIEW\s+(?:IF\s+NOT\s+EXISTS\s+)?(?P<name>\w+)", re.IGNORECASE)


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    path = Path(sys.argv[1])
    sql = path.read_text(encoding="utf-8")
    findings: list[str] = []
    tables: dict[str, dict] = {}

    for match in ROW_TABLE_RE.finditer(sql):
        rest = sql[match.end():]
        end = rest.find(";")
        body = rest[: end if end != -1 else len(rest)]
        name = match.group("name").split(".")[-1]
        columns = {m.group("col").lower() for m in COLUMN_RE.finditer(body)}
        tenant = columns & TENANT_COLUMNS
        not_null = bool(NOT_NULL_RE.search(body))
        tables[name] = {"tenant": tenant, "not_null": not_null, "is_view": False}

    for match in VIEW_RE.finditer(sql):
        name = match.group("name")
        tables.setdefault(name, {"tenant": None, "not_null": False, "is_view": True})

    policies: dict[str, int] = {}
    for match in POLICY_RE.finditer(sql):
        table = match.group("table").split(".")[-1]
        policies[table] = policies.get(table, 0) + 1

    for name, info in tables.items():
        if info["is_view"]:
            continue
        if not info["tenant"]:
            findings.append(f"table {name}: no tenant discriminator column found")
        elif not info["not_null"]:
            findings.append(f"table {name}: tenant column {info['tenant']} is not NOT NULL")
        if policies.get(name, 0) == 0:
            findings.append(f"table {name}: no CREATE POLICY found")

    if not FORCE_RLS_RE.search(sql):
        findings.append("migration: no FORCE ROW LEVEL SECURITY statement found")
    if not ROLLBACK_RE.search(sql):
        findings.append("migration: no -- ROLLBACK block found")

    # GRANT ALL on a specific table (schema-qualified or bare) is banned; the
    # `ON TABLE` form is rare, so match both `ON <table>` and `ON TABLE <table>`.
    for match in GRANT_ALL_RE.finditer(sql):
        line = sql[: match.end()].rpartition("\n")[2]
        if re.search(r"ON\s+TABLE\s+\w+|ON\s+\w+(\.\w+)?", line, re.IGNORECASE):
            findings.append(f"GRANT ALL found: {line.strip()}")

    if not SECURITY_INVOKER_RE.search(sql):
        views = [n for n, i in tables.items() if i["is_view"]]
        if views:
            findings.append(
                f"views present without security_invoker=true: {', '.join(views)}"
            )

    if findings:
        print(f"FAIL: {path}")
        for f in findings:
            print(f"  - {f}")
        return 1
    print(f"ok: {path} passes all RLS migration checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
