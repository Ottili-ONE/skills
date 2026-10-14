#!/usr/bin/env python3
"""Self-test for check_rls_migration.py: good example is clean, bad example fails,
missing file exits 2, --json is machine-readable, no args exits 2."""
import json
import subprocess
import sys
import tempfile
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


def test_json_output() -> None:
    """--json emits a machine-readable report and exits 0 on a clean migration."""
    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        good = t / "good.sql"
        good.write_text(EX.joinpath("good_migration.sql").read_text(), encoding="utf-8")
        rc, out = run(str(good), "--json")
        if rc != 0:
            print("FAIL: --json on a clean migration should exit 0")
            print(out)
            return 1
        try:
            data = json.loads(out)
        except json.JSONDecodeError:
            print("FAIL: --json output is not valid JSON:", out)
            return 1
        if data.get("status") != "ok" or data.get("files_checked") != 1:
            print("FAIL: --json status/files_checked wrong:", data)
            return 1
        print("ok: --json output is valid and correct")
        return 0


def test_usage_error() -> int:
    """No arguments exits 2."""
    rc, out = run()
    if rc != 2:
        print("FAIL: no args should exit 2, got", rc)
        return 1
    print("ok: usage error exits 2")
    return 0


EDGE_TESTS = [
    ("json output", test_json_output),
    ("usage error", test_usage_error),
]


def run_edge() -> int:
    failures = 0
    for _name, fn in EDGE_TESTS:
        try:
            failures += fn()
        except Exception as exc:  # noqa: BLE001
            print(f"FAIL: {_name} raised {exc!r}")
            failures += 1
    return failures


if __name__ == "__main__":
    rc = main()
    if rc != 0:
        raise SystemExit(rc)
    rc = run_edge()
    raise SystemExit(rc)
