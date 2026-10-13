#!/usr/bin/env python3
"""Static gate for a Postgres migration that touches a tenant-scoped table.

Exit codes: 0 = PASS, 1 = findings, 2 = malformed input.
Usage: check_rls_migration.py <migration.sql> [<migration.sql> ...]
"""
import re
import sys
from pathlib import Path

# A tenant discriminator may be named any of these; the checker accepts any of them.
TENANT_RE = re.compile(r"\b(tenant_id|organization_id|org_id|workspace_id|namespace)\b",
                       re.IGNORECASE)
FORCE_RE = re.compile(r"FORCE\s+ROW\s+LEVEL\s+SECURITY", re.IGNORECASE)
ENABLE_RE = re.compile(r"(?:ENABLE|DISABLE)\s+ROW\s+LEVEL\s+SECURITY", re.IGNORECASE)
GRANT_ALL_RE = re.compile(r"GRANT\s+ALL\b", re.IGNORECASE)
ROLLBACK_RE = re.compile(r"--\s*ROLLBACK", re.IGNORECASE)
SECURITY_INVOKER_RE = re.compile(r"security_invoker\s*=\s*(true|false)", re.IGNORECASE)
TABLE_RE = re.compile(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([a-zA-Z_][\w.]*)",
                      re.IGNORECASE)
POLICY_RE = re.compile(r"CREATE\s+POLICY\s+([a-zA-Z_][\w]*)", re.IGNORECASE)


def scan(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    findings: list[str] = []
    tables = TABLE_RE.findall(text)

    if not tables:
        findings.append("no CREATE TABLE statement found; is this a tenant migration?")
        return findings

    for table in tables:
        base = table.split(".")[-1]
        if not TENANT_RE.search(text):
            findings.append(f"{table}: no tenant discriminator column "
                            f"(tenant_id/organization_id/namespace)")
        if not POLICY_RE.search(text):
            findings.append(f"{table}: no CREATE POLICY for tenant isolation")
        if not ENABLE_RE.search(text):
            findings.append(f"{table}: missing ENABLE ROW LEVEL SECURITY")
        if not FORCE_RE.search(text):
            findings.append(f"{table}: missing FORCE ROW LEVEL SECURITY (owner would bypass RLS)")
        if GRANT_ALL_RE.search(text):
            findings.append(f"{table}: GRANT ALL on a protected table overrides the policy grant")
        if not ROLLBACK_RE.search(text):
            findings.append(f"{table}: no -- ROLLBACK block")
        # A view must declare security_invoker = true or it runs as the owner.
        if re.search(r"CREATE\s+(?:MATERIALIZED\s+)?VIEW", text, re.IGNORECASE):
            m = SECURITY_INVOKER_RE.search(text)
            if not m or m.group(1).lower() != "true":
                findings.append(f"{table}: view without security_invoker = true bypasses RLS")
    return findings


def main() -> int:
    args = sys.argv[1:]
    if not args:
        sys.stderr.write("usage: check_rls_migration.py <migration.sql> [...]\n")
        return 2
    failures = 0
    malformed = False
    for path in args:
        p = Path(path)
        if not p.is_file():
            print(f"FAIL: {path}: file not found", file=sys.stderr)
            malformed = True
            continue
        findings = scan(p)
        if findings:
            failures += 1
            print(f"FAIL: {path}")
            for f in findings:
                print(f"  - {f}", file=sys.stderr)
        else:
            print(f"ok: {path}")
    if malformed:
        return 2
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
