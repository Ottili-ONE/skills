#!/usr/bin/env python3
"""Offline checker for the real platform outbox envelope.

The platform's durable outbox is `audit_outbox` (services/audit/migrations/
002-audit-outbox.up.sql). Its `record` column carries the full `EventOutboxRecord`
envelope (packages/contracts-core/src/generated/types.ts). This checker verifies, without
a database, that the envelope is complete and tenant-scoped:

  * `company_id` is on every row and is part of the PRIMARY KEY, so idempotency is
    scoped per tenant (a retry in company B can never re-deliver company A's event);
  * the `record` JSON carries the full 15-field envelope with the pinned
    `schema_version` `ottili.outbox-record/v1`;
  * the envelope can reach the `dead_letter` state (the platform has no separate
    poison_outbox table — audit_outbox is append-only — so a poison row is dead-lettered
    in place, and a schema that cannot express that blocks the queue forever).

Exit 0 = clean, 1 = findings, 2 = malformed input.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

OUTBOX_TABLE_RE = re.compile(
    r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?P<name>\w+)", re.IGNORECASE
)
COL_RE = re.compile(r"^\s*(?P<col>\w+)\s+(?P<rest>.+)$", re.MULTILINE)

PLATFORM_OUTBOX_TABLE = "audit_outbox"
PLATFORM_ENVELOPE_FIELDS = (
    "schema_version",
    "outbox_id",
    "company_id",
    "event_id",
    "event_type",
    "partition_key",
    "state",
    "attempts",
    "created_at",
    "dispatched_at",
    "payload_digest",
    "last_error_code",
    "available_at",
    "dispatch_lease_expires_at",
    "dispatch_fence",
)
PLATFORM_ENVELOPE_SCHEMA_VERSION = "ottili.outbox-record/v1"


def _table_bodies(sql: str) -> dict[str, str]:
    """Map lower-cased table name -> CREATE TABLE body (up to the terminating ;)."""
    tables: dict[str, str] = {}
    for m in OUTBOX_TABLE_RE.finditer(sql):
        rest = sql[m.end():]
        end = rest.find(";")
        body = rest[: end if end != -1 else len(rest)]
        tables[m.group("name").lower()] = body
    return tables


def _platform_outbox_body(sql: str) -> str | None:
    """Return the CREATE TABLE body for the platform outbox, or None."""
    return _table_bodies(sql).get(PLATFORM_OUTBOX_TABLE.lower())


def check_platform_outbox(sql: str) -> list[str]:
    """Check the real platform outbox envelope. See module docstring."""
    findings: list[str] = []
    body = _platform_outbox_body(sql)
    if body is None:
        return findings
    cols = {m.group("col").lower(): m.group("rest") for m in COL_RE.finditer(body)}

    if "company_id" not in cols:
        findings.append(f"{PLATFORM_OUTBOX_TABLE}: no company_id tenant column on every row")
    if "outbox_id" not in cols:
        findings.append(f"{PLATFORM_OUTBOX_TABLE}: no outbox_id column")
    if "record" not in cols:
        findings.append(f"{PLATFORM_OUTBOX_TABLE}: no record column carrying the envelope")

    pk = re.search(r"PRIMARY\s+KEY\s*\((?P<cols>[^)]+)\)", body, re.IGNORECASE)
    if not pk:
        findings.append(f"{PLATFORM_OUTBOX_TABLE}: no PRIMARY KEY (idempotency not enforced)")
    elif ("company_id" not in pk.group("cols").lower()
          or "outbox_id" not in pk.group("cols").lower()):
        findings.append(
            f"{PLATFORM_OUTBOX_TABLE}: PRIMARY KEY {pk.group('cols')} is not scoped on "
            f"company_id + outbox_id (idempotency would not be tenant-scoped)")

    inserts = re.findall(
        r"INSERT\s+INTO\s+audit_outbox\b.*?VALUES\s*\((?P<vals>.*?)\);",
        sql, re.IGNORECASE | re.DOTALL,
    )
    if not inserts:
        findings.append(f"{PLATFORM_OUTBOX_TABLE}: no INSERT example to validate the envelope")
    for vals in inserts:
        m = re.search(r"['\"](\{.*schema_version.*\})['\"]", vals, re.DOTALL)
        if not m:
            findings.append(f"{PLATFORM_OUTBOX_TABLE}: INSERT has no JSON record envelope")
            continue
        env = m.group(1)
        for field in PLATFORM_ENVELOPE_FIELDS:
            if f'"{field}"' not in env:
                findings.append(
                    f"{PLATFORM_OUTBOX_TABLE}: record envelope missing field {field!r}")
        if f'"{PLATFORM_ENVELOPE_SCHEMA_VERSION}"' not in env:
            findings.append(
                f"{PLATFORM_OUTBOX_TABLE}: record schema_version is not "
                f"{PLATFORM_ENVELOPE_SCHEMA_VERSION!r}")
        if '"state"' not in env:
            findings.append(f"{PLATFORM_OUTBOX_TABLE}: record envelope has no state field")
        elif '"dead_letter"' not in env:
            findings.append(
                f"{PLATFORM_OUTBOX_TABLE}: record envelope never reaches the dead_letter state "
                f"(poison rows would block the queue forever)")
    return findings


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("outbox_sql", help="SQL file defining the platform outbox")
    ap.add_argument("--json", action="store_true",
                    help="emit machine-readable JSON instead of text")
    args = ap.parse_args()

    try:
        sql = Path(args.outbox_sql).read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"FAIL: {args.outbox_sql}: file not found", file=sys.stderr)
        return 2
    findings = check_platform_outbox(sql)

    if args.json:
        print(json.dumps({
            "status": "fail" if findings else "ok",
            "file": args.outbox_sql,
            "findings": findings,
        }, indent=2, sort_keys=True))
        return 1 if findings else 0

    if findings:
        print(f"FAIL: {args.outbox_sql}")
        for f in findings:
            print(f"  - {f}")
        return 1
    print(f"ok: {args.outbox_sql} platform outbox envelope is complete and tenant-scoped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
