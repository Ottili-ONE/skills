#!/usr/bin/env python3
"""Offline self-tests for check_outbox.py.

Embeds good/bad SQL fixtures and asserts the checker's exit code and findings.
Deterministic: no database, no network, no randomness.
Run: python3 skills/engineering/outbox-idempotency/scripts/check_outbox_test.py
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

CHECKER = Path(__file__).resolve().parent / "check_outbox.py"

GOOD_SQL = """\
-- Outbox schema + one-transaction write.
CREATE TABLE IF NOT EXISTS outbox (
    id           uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    idempotency_key text      NOT NULL UNIQUE,
    payload      jsonb       NOT NULL,
    created_at   timestamptz NOT NULL DEFAULT now(),
    sent_at      timestamptz,
    attempts     int         NOT NULL DEFAULT 0,
    last_error   text
);
CREATE TABLE poison_outbox (
    id           uuid        PRIMARY KEY,
    idempotency_key text      NOT NULL,
    payload      jsonb       NOT NULL,
    moved_at     timestamptz NOT NULL DEFAULT now()
);
BEGIN;
INSERT INTO accounts (id, balance) VALUES ('a1', 100);
INSERT INTO outbox (idempotency_key, payload)
  VALUES ('acct-a1-debit-001', '{"event":"account.debitted"}');
COMMIT;
"""

BAD_SQL = """\
-- Missing UNIQUE, missing attempts, poison rows deleted, separate transactions.
CREATE TABLE outbox (
    id uuid PRIMARY KEY,
    idempotency_key text NOT NULL,
    payload jsonb NOT NULL
);
INSERT INTO accounts (id) VALUES ('a1');
INSERT INTO outbox (idempotency_key, payload) VALUES ('k1', '{}');
DELETE FROM poison_outbox;
"""

GOOD_POLLER = """\
SELECT id, idempotency_key, payload
FROM outbox
WHERE sent_at IS NULL
ORDER BY created_at
LIMIT 50
FOR UPDATE SKIP LOCKED;
UPDATE outbox SET sent_at = now() WHERE id = $1;
"""

BAD_POLLER = """\
SELECT id, payload FROM outbox WHERE sent_at IS NULL LIMIT 50 FOR UPDATE SKIP LOCKED;
DELETE FROM outbox WHERE attempts >= 5;
"""


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(CHECKER), *args],
        capture_output=True,
        text=True,
        timeout=30,
    )


def write(tmp: Path, name: str, content: str) -> str:
    p = tmp / name
    p.write_text(content, encoding="utf-8")
    return str(p)


def main() -> int:
    failures = 0
    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        good_sql = write(t, "good.sql", GOOD_SQL)
        bad_sql = write(t, "bad.sql", BAD_SQL)
        good_poller = write(t, "good_poller.sql", GOOD_POLLER)
        bad_poller = write(t, "bad_poller.sql", BAD_POLLER)

        r = run(good_sql)
        if r.returncode != 0:
            print("FAIL: good SQL should pass")
            print(r.stdout, r.stderr)
            failures += 1
        else:
            print("ok: good SQL passes")

        r = run(bad_sql)
        if r.returncode != 1:
            print("FAIL: bad SQL should fail")
            print(r.stdout, r.stderr)
            failures += 1
        else:
            print("ok: bad SQL fails as expected")

        r = run(good_sql, "--poller", good_poller)
        if r.returncode != 0:
            print("FAIL: good SQL + good poller should pass")
            print(r.stdout, r.stderr)
            failures += 1
        else:
            print("ok: good SQL + good poller passes")

        r = run(good_sql, "--poller", bad_poller)
        if r.returncode != 1:
            print("FAIL: good SQL + bad poller should fail")
            print(r.stdout, r.stderr)
            failures += 1
        else:
            print("ok: good SQL + bad poller fails as expected")

    if failures:
        print(f"\n{failures} test(s) failed")
        return 1
    print("\nall tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
