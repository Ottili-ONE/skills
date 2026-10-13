#!/usr/bin/env python3
"""Self-test for check_outbox.py: good example is clean, bad examples fail, missing file exits 2."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECK = ROOT / "scripts" / "check_outbox.py"
EX = ROOT / "references" / "examples"


def run(*args: str) -> tuple[int, str]:
    p = subprocess.run([sys.executable, str(CHECK), *args],
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


if __name__ == "__main__":
    sys.exit(main())
