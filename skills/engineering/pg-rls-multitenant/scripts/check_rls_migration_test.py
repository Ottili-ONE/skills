#!/usr/bin/env python3
"""Offline self-tests for check_rls_migration.py.

Embeds good/bad SQL fixtures and asserts the checker's exit code and
findings. Deterministic: no database, no network, no randomness.
Run: python3 skills/engineering/pg-rls-multitenant/scripts/check_rls_migration_test.py
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

CHECKER = Path(__file__).resolve().parent / "check_rls_migration.py"

GOOD = """\
-- Migration V20261007_001: add tenant_isolated_notes with RLS.
CREATE TABLE IF NOT EXISTS tenant_isolated_notes (
    id         uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id  uuid        NOT NULL,
    body       text        NOT NULL
);
CREATE POLICY tenant_isolation ON tenant_isolated_notes
    AS PERMISSIVE FOR SELECT TO web_app
    USING (tenant_id = current_setting('app.current_tenant')::uuid);
ALTER TABLE tenant_isolated_notes ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_isolated_notes FORCE ROW LEVEL SECURITY;
GRANT SELECT, INSERT ON tenant_isolated_notes TO web_app;
-- ROLLBACK
-- DROP POLICY IF EXISTS tenant_isolation ON tenant_isolated_notes;
-- DROP TABLE IF EXISTS tenant_isolated_notes;
"""

BAD = """\
CREATE TABLE bad_notes (
    id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id  uuid,
    body       text
);
CREATE POLICY nothing ON bad_notes FOR SELECT TO web_app USING (true);
ALTER TABLE bad_notes ENABLE ROW LEVEL SECURITY;
GRANT ALL ON bad_notes TO web_app;
"""

VIEW_BAD = """\
CREATE VIEW public.active_notes AS SELECT * FROM tenant_isolated_notes;
"""

VIEW_GOOD = """\
CREATE VIEW public.active_notes
    security_invoker = true
    AS SELECT * FROM tenant_isolated_notes;
"""


def run(sql: str) -> tuple[int, str]:
    with tempfile.NamedTemporaryFile("w", suffix=".sql", delete=False) as f:
        f.write(sql)
        path = f.name
    try:
        proc = subprocess.run(
            [sys.executable, str(CHECKER), path],
            capture_output=True, text=True,
        )
        return proc.returncode, (proc.stdout + proc.stderr)
    finally:
        Path(path).unlink(missing_ok=True)


def main() -> int:
    failures = 0

    def check(name: str, sql: str, want_code: int, must_contain: list[str]) -> None:
        nonlocal failures
        code, out = run(sql)
        ok = code == want_code and all(m in out for m in must_contain)
        if not ok:
            failures += 1
            print(f"FAIL: {name}")
            print(f"  exit={code} want={want_code}")
            print(f"  output={out!r}")
            for m in must_contain:
                if m not in out:
                    print(f"  missing: {m!r}")
        else:
            print(f"ok: {name}")

    check("good migration passes", GOOD, 0, ["ok:"])
    check("bad migration fails", BAD, 1, ["FAIL:", "not NOT NULL", "GRANT ALL", "no FORCE"])
    check("view without security_invoker fails", VIEW_BAD, 1, ["security_invoker"])
    check("view with security_invoker passes", VIEW_GOOD, 0, ["ok:"])

    if failures:
        print(f"\n{failures} test(s) failed")
        return 1
    print("\nall tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
