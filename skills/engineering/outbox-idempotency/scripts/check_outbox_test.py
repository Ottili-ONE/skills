#!/usr/bin/env python3
"""Self-test for check_outbox.py: good example is clean, bad examples fail, missing file exits 2."""
import subprocess
import sys
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECK = ROOT / "scripts" / "check_outbox.py"
PCHECK = ROOT / "scripts" / "check_outbox_platform.py"
EX = ROOT / "references" / "examples"


def run(*args: str) -> tuple[int, str]:
    p = subprocess.run([sys.executable, str(CHECK), *args],
                       capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def run_platform(path: str) -> tuple[int, str]:
    """Run the platform envelope checker directly (it has its own CLI)."""
    p = subprocess.run([sys.executable, str(PCHECK), path],
                       capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def main() -> int:
    failures = []
    good, out = run(str(EX / "good_outbox.sql"), "--poller", str(EX / "good_poller.py"))
    if good != 0:
        failures.append(f"good outbox must exit 0, got {good}\n{out}")

    bad, out = run(str(EX / "bad_no_unique.sql"))
    if bad != 1 or "idempotency_key" not in out:
        failures.append(f"bad_no_unique must exit 1 mentioning idempotency_key, got {bad}\n{out}")

    bad, out = run(str(EX / "bad_delete_poison.sql"))
    if bad != 1 or "DELETE FROM poison_outbox" not in out:
        failures.append(f"bad_delete_poison must flag DELETE FROM poison_outbox, got {bad}\n{out}")

    bad, out = run(str(EX / "good_outbox.sql"), "--poller", str(EX / "bad_poller.py"))
    if bad != 1 or "SKIP LOCKED" not in out:
        failures.append(f"bad_poller must flag missing SKIP LOCKED, got {bad}\n{out}")

    bad, out = run(str(EX / "good_outbox.sql"), "--poller", str(EX / "bad_limit_order.py"))
    if bad != 1 or "ORDER BY created_at" not in out:
        failures.append(f"bad_limit_order must flag ORDER BY on wrong column, got {bad}\n{out}")

    bad, out = run(str(EX / "good_outbox.sql"), "--poller", str(EX / "bad_no_max_attempts.py"))
    if bad != 1 or "max_attempts" not in out:
        failures.append(f"bad_no_max_attempts must flag missing poison threshold, got {bad}\n{out}")

    missing, out = run(str(EX / "nope.sql"))
    if missing != 2:
        failures.append(f"missing file must exit 2, got {missing}\n{out}")

    if failures:
        for f in failures:
            print(f"FAIL: {f}", file=sys.stderr)
        return 1
    print("ok: outbox checker self-test (good, 3 bad, missing)")
    return 0




HOSTILE_PLATFORM = [
    "hostile_no_company_id.sql",
    "hostile_tenant_leak.sql",
    "hostile_missing_dead_letter.sql",
]


def test_platform_hostile() -> int:
    """The platform envelope checker must fail every hostile fixture and pass the good one."""
    failures = 0
    rc, out = run_platform(str(EX / "good_outbox.sql"))
    if rc != 0:
        print("FAIL: good platform envelope must exit 0")
        print(out)
        failures += 1
    else:
        print("ok: good platform envelope passes")
    for h in HOSTILE_PLATFORM:
        rc, out = run_platform(str(EX / h))
        if rc != 1 or "FAIL" not in out:
            print(f"FAIL: {h} must exit 1 and print FAIL")
            print(out)
            failures += 1
        else:
            print(f"ok: {h} flagged by the platform envelope checker")
    return failures


EDGE = [
    ("no BEGIN/COMMIT blocks", "no BEGIN/COMMIT transaction blocks found"),
    ("outbox INSERT alone in a block", "outbox INSERT without a business write"),
    ("missing file", None),  # special-cased: exit 2
]


def _run_edge() -> int:
    failures = 0
    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)

        # No BEGIN/COMMIT blocks at all -> cannot prove same-transaction writes.
        f = t / "no_tx.sql"
        f.write_text(
            "CREATE TABLE outbox (id uuid PRIMARY KEY, idempotency_key text NOT NULL UNIQUE, "
            "payload jsonb NOT NULL, created_at timestamptz NOT NULL DEFAULT now(), "
            "sent_at timestamptz, attempts int NOT NULL DEFAULT 0, last_error text);\n"
            "CREATE TABLE poison_outbox (like outbox);\n"
        )
        rc, out = run(str(f))
        if rc != 1 or "BEGIN/COMMIT" not in out:
            print("FAIL: no-transaction SQL should be flagged")
            print(out)
            failures += 1
        else:
            print("ok: no BEGIN/COMMIT blocks flagged")

        # Outbox INSERT with no business write in the same block.
        f = t / "solo.sql"
        f.write_text(
            "CREATE TABLE outbox (id uuid PRIMARY KEY, idempotency_key text NOT NULL UNIQUE, "
            "payload jsonb NOT NULL, created_at timestamptz NOT NULL DEFAULT now(), "
            "sent_at timestamptz, attempts int NOT NULL DEFAULT 0, last_error text);\n"
            "CREATE TABLE poison_outbox (like outbox);\n"
            "BEGIN;\n"
            "INSERT INTO outbox (idempotency_key, payload) VALUES ('k1', '{}');\n"
            "COMMIT;\n"
        )
        rc, out = run(str(f))
        if rc != 1 or "business write" not in out:
            print("FAIL: outbox-only transaction should be flagged")
            print(out)
            failures += 1
        else:
            print("ok: outbox-only transaction flagged")

        # --json on a failing file is machine-readable.
        rc, out = run(str(f), "--json")
        if rc != 1:
            print("FAIL: --json on a failing file should exit 1")
            print(out)
            failures += 1
        else:
            try:
                data = json.loads(out)
                if data.get("status") != "fail" or not data.get("findings"):
                    print("FAIL: --json status/findings wrong:", data)
                    failures += 1
                else:
                    print("ok: --json machine-readable on failure")
            except json.JSONDecodeError:
                print("FAIL: --json output is not valid JSON:", out)
                failures += 1
    return failures


if __name__ == "__main__":
    rc = main()
    if rc != 0:
        raise SystemExit(rc)
    rc = test_platform_hostile()
    if rc != 0:
        raise SystemExit(rc)
    rc = _run_edge()
    raise SystemExit(rc)
