#!/usr/bin/env python3
"""Offline checker for the transactional outbox invariants.

Verifies, without a database, the rules the outbox-idempotency skill mandates:
  1. an `outbox` table exists with a UNIQUE NOT NULL `idempotency_key`
  2. the poller query contains `ORDER BY created_at` and `FOR UPDATE SKIP LOCKED`
  3. a poison threshold exists (`attempts >= N` -> move to poison_outbox)
  4. the poison table keeps the original `idempotency_key`
  5. no DELETE targets `poison_outbox`
  6. the business write and the outbox INSERT are in the same transaction block

Usage:
  python3 check_outbox.py <outbox-sql-file> [--poller <poller-source-file>]
Exit 0 = all checks pass; 1 = findings; 2 = usage error.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

OUTBOX_TABLE_RE = re.compile(
    r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?P<name>\w+)", re.IGNORECASE
)
COL_RE = re.compile(r"^\s*(?P<col>\w+)\s+(?P<rest>.+)$", re.MULTILINE)
UNIQUE_RE = re.compile(r"UNIQUE\s*\((?P<cols>[^)]+)\)", re.IGNORECASE)
NOTNULL_RE = re.compile(r"NOT\s+NULL", re.IGNORECASE)
ORDERBY_RE = re.compile(r"ORDER\s+BY\s+created_at", re.IGNORECASE)
SKIPLOCK_RE = re.compile(r"FOR\s+UPDATE\s+SKIP\s+LOCKED", re.IGNORECASE)
POISON_RE = re.compile(r"poison_outbox", re.IGNORECASE)
POISON_DELETE_RE = re.compile(r"DELETE\s+FROM\s+poison_outbox", re.IGNORECASE)
TXBEGIN_RE = re.compile(r"^\s*BEGIN\b", re.IGNORECASE | re.MULTILINE)
TXCOMMIT_RE = re.compile(r"^\s*COMMIT\b", re.IGNORECASE | re.MULTILINE)


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def _table_bodies(sql: str) -> dict[str, str]:
    """Map lower-cased table name -> CREATE TABLE body (up to the terminating ;)."""
    tables: dict[str, str] = {}
    for m in OUTBOX_TABLE_RE.finditer(sql):
        rest = sql[m.end():]
        end = rest.find(";")
        body = rest[: end if end != -1 else len(rest)]
        tables[m.group("name").lower()] = body
    return tables


def check_outbox_sql(sql: str) -> list[str]:
    findings: list[str] = []
    tables = _table_bodies(sql)

    if "outbox" not in tables:
        findings.append("outbox table not found")
        return findings

    body = tables["outbox"]
    cols = {m.group("col").lower(): m.group("rest") for m in COL_RE.finditer(body)}

    if "idempotency_key" not in cols:
        findings.append("outbox: no idempotency_key column")
    else:
        if not NOTNULL_RE.search(cols["idempotency_key"]):
            findings.append("outbox: idempotency_key is not NOT NULL")
        # UNIQUE may be table-level `UNIQUE (col, ...)` or column-level
        # `idempotency_key text NOT NULL UNIQUE`.
        uq = UNIQUE_RE.search(body)
        key_line = cols.get("idempotency_key", "")
        if not uq and not re.search(r"\bUNIQUE\b", key_line, re.IGNORECASE):
            findings.append("outbox: no UNIQUE constraint (idempotency_key must be unique)")
        elif uq and "idempotency_key" not in uq.group("cols").lower() and not re.search(
            r"\bUNIQUE\b", key_line, re.IGNORECASE
        ):
            findings.append("outbox: UNIQUE constraint does not include idempotency_key")

    if "attempts" not in cols:
        findings.append("outbox: no attempts column (poison threshold cannot be expressed)")
    if "sent_at" not in cols:
        findings.append("outbox: no sent_at column (poller cannot mark rows published)")

    if not POISON_RE.search(sql):
        findings.append("no poison_outbox destination referenced")
    if POISON_DELETE_RE.search(sql):
        findings.append("DELETE FROM poison_outbox found: poison rows must be moved, never deleted")

    # Same-transaction check: every BEGIN..COMMIT block that inserts into outbox
    # must also insert into a business table.
    blocks = TXBEGIN_RE.split(sql)
    for blk in blocks[1:]:
        seg = TXCOMMIT_RE.split(blk, maxsplit=1)[0]
        has_outbox = re.search(r"INSERT\s+INTO\s+outbox\b", seg, re.IGNORECASE)
        has_business = re.search(
            r"INSERT\s+INTO\s+(?!outbox\b)(?!poison_outbox\b)", seg, re.IGNORECASE
        )
        if has_outbox and not has_business:
            findings.append(
                "outbox INSERT without a business write in the same transaction block"
            )

    return findings


def check_poller(source: str) -> list[str]:
    findings: list[str] = []
    if not ORDERBY_RE.search(source):
        findings.append("poller: missing ORDER BY created_at (delivery order undefined)")
    if not SKIPLOCK_RE.search(source):
        findings.append("poller: missing FOR UPDATE SKIP LOCKED (parallel pollers block)")
    if not re.search(r"UPDATE\s+outbox\s+SET\s+sent_at", source, re.IGNORECASE):
        findings.append("poller: no UPDATE sent_at after publish (crash => duplicate publish)")
    if re.search(r"DELETE\s+FROM\s+outbox\b", source, re.IGNORECASE):
        findings.append("poller: DELETE FROM outbox found (rows must be moved to poison, never deleted)")
    return findings


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("outbox_sql", help="SQL file defining the outbox schema and writes")
    ap.add_argument("--poller", help="optional poller source file to check")
    args = ap.parse_args()

    sql = _read(Path(args.outbox_sql))
    findings = check_outbox_sql(sql)
    if args.poller:
        findings.extend(check_poller(_read(Path(args.poller))))

    if findings:
        print(f"FAIL: {args.outbox_sql}")
        for f in findings:
            print(f"  - {f}")
        return 1
    print(f"ok: {args.outbox_sql} passes all outbox checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
