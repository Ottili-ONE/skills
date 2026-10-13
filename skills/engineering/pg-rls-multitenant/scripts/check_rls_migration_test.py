#!/usr/bin/env python3
"""Self-test for check_rls_migration.py: good example is clean, bad example fails, missing file exits 2."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECK = ROOT / "scripts" / "check_rls_migration.py"
EX = ROOT / "references" / "examples"


def run(*paths: str) -> tuple[int, str]:
    p = subprocess.run([sys.executable, str(CHECK), *paths],
                       capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def main() -> int:
    failures = []
    good, out = run(str(EX / "good_migration.sql"))
    if good != 0:
        failures.append(f"good migration must exit 0, got {good}\n{out}")

    bad, out = run(str(EX / "bad_migration.sql"))
    if bad != 1:
        failures.append(f"bad migration must exit 1, got {bad}\n{out}")
    else:
        for needle in ("FORCE ROW LEVEL SECURITY", "GRANT ALL", "ROLLBACK"):
            if needle not in out:
                failures.append(f"bad migration output must mention {needle!r}\n{out}")

    missing, out = run(str(EX / "does-not-exist.sql"))
    if missing != 2:
        failures.append(f"missing file must exit 2, got {missing}\n{out}")

    if failures:
        for f in failures:
            print(f"FAIL: {f}", file=sys.stderr)
        return 1
    print("ok: pg-rls migration checker self-test (good, bad, missing)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
