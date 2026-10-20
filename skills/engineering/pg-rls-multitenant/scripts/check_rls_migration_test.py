#!/usr/bin/env python3
"""Self-test for check_rls_migration.py.

The checker is per-table and keyed on the single product GUC `app.company_id`
(see docs/truth/REPAIR_LOG.md, D-003). It must:
  * PASS the three real hq migrations,
  * FAIL the three hostile fixtures (no FORCE / no company_id / GRANT ALL),
  * PASS the skill's own good example (now written to the product standard),
  * FAIL the skill's own bad example,
  * exit 2 on a missing file and on no args,
  * emit machine-readable --json.
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECK = ROOT / "scripts" / "check_rls_migration.py"
EX = ROOT / "references" / "examples"

# The hq-v2 checkout lives in another repository, so it is only present on
# hosts that also have that repository. Point OTTLI_HQ_REPO at it to check the
# real corpus; everywhere else the self-test proves the documented behaviour
# for a missing file (exit 2) instead of failing on a foreign path.
HQ_ROOT = Path(os.environ.get("OTTLI_HQ_REPO", "/srv/ottili/repo/hq-v2"))

# Three real hq migrations, verified 2026-10-16 to use company_id + app.company_id.
HQ = [
    "modules/reports-intelligence/migrations/"
    "20261002091600_reports_intelligence_saved_report.sql",
    "modules/reports-intelligence/migrations/"
    "20261002091630_reports_intelligence_signal_threshold.sql",
    "modules/procure-to-stock/migrations/"
    "20261010000000_hq_procure_to_stock_r3_04_audit.sql",
]

HOSTILE = [
    "hostile_1_no_force.sql",
    "hostile_2_no_company_id.sql",
    "hostile_3_grant_all.sql",
]


def run(*paths: str) -> tuple[int, str]:
    p = subprocess.run([sys.executable, str(CHECK), *paths],
                       capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def main() -> int:
    failures = []

    good, out = run(str(EX / "good_migration.sql"))
    if good != 0:
        failures.append(f"good migration must exit 0, got {good}\n{out}")

    for h in HOSTILE:
        rc, out = run(str(EX / h))
        if rc != 1:
            failures.append(f"{h} must exit 1, got {rc}\n{out}")
        elif "FAIL" not in out:
            failures.append(f"{h} output must say FAIL\n{out}")

    hq_paths = [HQ_ROOT / m for m in HQ]
    corpus_present = all(p.is_file() for p in hq_paths)
    if corpus_present:
        for m in hq_paths:
            rc, out = run(str(m))
            if rc != 0:
                failures.append(f"real hq migration {m} must exit 0, got {rc}\n{out}")
    else:
        absent = str(hq_paths[0])
        rc, out = run(absent)
        if rc != 2:
            failures.append(f"missing migration {absent} must exit 2, got {rc}\n{out}")
        elif "not found" not in out:
            failures.append(f"missing migration {absent} must report 'not found'\n{out}")
        print(
            f"note: the hq-v2 corpus ({HQ_ROOT}) is not on this host; "
            "checked the missing-file contract instead",
            file=sys.stderr,
        )

    # All three hostile at once still fails (exit 1, not 0).
    rc, out = run(*[str(EX / h) for h in HOSTILE])
    if rc != 1:
        failures.append(f"all hostile together must exit 1, got {rc}\n{out}")

    bad, out = run(str(EX / "bad_migration.sql"))
    if bad != 1:
        failures.append(f"bad migration must exit 1, got {bad}\n{out}")
    else:
        for needle in ("FORCE ROW LEVEL SECURITY", "GRANT ALL"):
            if needle not in out:
                failures.append(f"bad migration output must mention {needle!r}\n{out}")

    missing, out = run(str(EX / "does-not-exist.sql"))
    if missing != 2:
        failures.append(f"missing file must exit 2, got {missing}\n{out}")

    if failures:
        for f in failures:
            print(f"FAIL: {f}", file=sys.stderr)
        return 1
    corpus = "3 real hq PASS" if corpus_present else "missing-file contract"
    print(f"ok: pg-rls migration checker self-test ({corpus}, 3 hostile FAIL)")
    return 0


def test_json_output() -> None:
    """--json emits a machine-readable report and exits 0 on a clean migration."""
    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        good = t / "good.sql"
        good.write_text(EX.joinpath("good_migration.sql").read_text(), encoding="utf-8")
        rc, out = run(str(good), "--json")
        assert rc == 0, f"--json on a clean migration should exit 0, got {rc}: {out}"
        try:
            data = json.loads(out)
        except json.JSONDecodeError as exc:
            raise AssertionError(f"--json output is not valid JSON: {out}") from exc
        assert data.get("status") == "ok", f"--json status wrong: {data}"
        assert data.get("files_checked") == 1, f"--json files_checked wrong: {data}"
        print("ok: --json output is valid and correct")


def test_usage_error() -> None:
    """No arguments exits 2."""
    rc, out = run()
    assert rc == 2, f"no args should exit 2, got {rc}: {out}"
    print("ok: usage error exits 2")


EDGE_TESTS = [
    ("json output", test_json_output),
    ("usage error", test_usage_error),
]


def run_edge() -> int:
    """Standalone runner for the edge cases."""
    failures = 0
    for _name, fn in EDGE_TESTS:
        try:
            fn()
        except AssertionError as exc:
            print(f"FAIL: {_name}: {exc}")
            failures += 1
        else:
            print(f"ok: {_name}")
    return failures


if __name__ == "__main__":
    rc = main()
    if rc != 0:
        raise SystemExit(rc)
    rc = run_edge()
    raise SystemExit(rc)
