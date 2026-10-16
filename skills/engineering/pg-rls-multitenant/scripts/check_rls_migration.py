#!/usr/bin/env python3
"""Static gate for a Postgres migration that touches tenant-scoped tables.

Every tenant table in the migration must, per-table:
  (a) be created with ENABLE + FORCE ROW LEVEL SECURITY,
  (b) carry a tenant policy keyed on the single GUC the product repos use, and
  (c) carry a ``company_id`` column.

The tenant GUC is ``app.company_id``. Verified 2026-10-16 across hq-v2:
``current_setting('app.company_id', true)`` appears 995 times; the legacy
candidates ``app.current_company`` (51) and ``app.current_company_id`` (29)
belong to older modules and are NOT the product standard. See
docs/truth/REPAIR_LOG.md.

Exit codes: 0 = PASS, 1 = findings, 2 = malformed input.
Usage: check_rls_migration.py <migration.sql> [<migration.sql> ...]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# The single GUC name the product repos actually use to carry the tenant
# discriminator inside RLS USING / WITH CHECK expressions.
TENANT_GUC = "app.company_id"

CREATE_TABLE_STMT_RE = re.compile(
    r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?"
    r"(?P<name>[a-zA-Z_][\w.]*)\s*\((?P<body>.*?)\)\s*;",
    re.IGNORECASE | re.DOTALL,
)
ENABLE_RE = re.compile(
    r"ALTER\s+TABLE\s+(?P<name>[a-zA-Z_][\w.]*)\s+ENABLE\s+ROW\s+LEVEL\s+SECURITY",
    re.IGNORECASE,
)
FORCE_RE = re.compile(
    r"ALTER\s+TABLE\s+(?P<name>[a-zA-Z_][\w.]*)\s+FORCE\s+ROW\s+LEVEL\s+SECURITY",
    re.IGNORECASE,
)
# A CREATE POLICY statement runs to its terminating semicolon so the USING /
# WITH CHECK expressions (where the GUC lives) are captured with the policy.
POLICY_STMT_RE = re.compile(
    r"CREATE\s+POLICY\s+\S+\s+ON\s+(?P<name>[a-zA-Z_][\w.]*)\b.*?;",
    re.IGNORECASE | re.DOTALL,
)
COMPANY_ID_COL_RE = re.compile(r"\bcompany_id\b", re.IGNORECASE)
GUC_RE = re.compile(
    r"current_setting\(\s*['\"]" + re.escape(TENANT_GUC) + r"['\"]"
)
GRANT_ALL_RE = re.compile(r"GRANT\s+ALL\b", re.IGNORECASE)


def _base(name: str) -> str:
    return name.split(".")[-1]


def scan(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    findings: list[str] = []

    tables = list(CREATE_TABLE_STMT_RE.finditer(text))
    if not tables:
        findings.append("no CREATE TABLE statement found; is this a tenant migration?")
        return findings

    enabled = {_base(m.group("name")) for m in ENABLE_RE.finditer(text)}
    forced = {_base(m.group("name")) for m in FORCE_RE.finditer(text)}
    # table base name -> list of policy bodies that target it
    policies: dict[str, list[str]] = {}
    for m in POLICY_STMT_RE.finditer(text):
        policies.setdefault(_base(m.group("name")), []).append(m.group(0))

    for m in tables:
        base = _base(m.group("name"))
        body = m.group("body")

        # (c) the table must carry a company_id discriminator column
        if not COMPANY_ID_COL_RE.search(body):
            findings.append(
                f"{base}: no company_id tenant discriminator column"
            )

        # (a) ENABLE + FORCE ROW LEVEL SECURITY, per-table
        if base not in enabled:
            findings.append(
                f"{base}: missing ENABLE ROW LEVEL SECURITY"
            )
        elif base not in forced:
            findings.append(
                f"{base}: missing FORCE ROW LEVEL SECURITY (owner would bypass RLS)"
            )

        # (b) a tenant policy keyed on the product GUC
        bodies = policies.get(base, [])
        if not bodies:
            findings.append(
                f"{base}: no CREATE POLICY for tenant isolation"
            )
        elif not any(GUC_RE.search(b) for b in bodies):
            findings.append(
                f"{base}: tenant policy is not keyed on current_setting("
                f"'{TENANT_GUC}')"
            )

    if GRANT_ALL_RE.search(text):
        findings.append("GRANT ALL on a protected table overrides the policy grant")
    return findings


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("migrations", nargs="+", help="migration SQL file(s) to check")
    ap.add_argument("--json", action="store_true",
                    help="emit machine-readable JSON instead of text")
    args = ap.parse_args()

    failures = 0
    malformed = False
    reports: list[dict] = []
    for path in args.migrations:
        p = Path(path)
        if not p.is_file():
            print(f"FAIL: {path}: file not found", file=sys.stderr)
            malformed = True
            continue
        findings = scan(p)
        reports.append({"file": str(p.resolve()), "findings": findings})
        if findings:
            failures += 1
            if not args.json:
                print(f"FAIL: {path}")
            for f in findings:
                print(f"  - {f}", file=sys.stderr)
        elif not args.json:
            print(f"ok: {path}")
    if args.json:
        print(json.dumps({
            "status": "fail" if (failures or malformed) else "ok",
            "files_checked": len(args.migrations),
            "failures": failures,
            "malformed": malformed,
            "reports": reports,
        }, indent=2, sort_keys=True))
    if malformed:
        return 2
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
