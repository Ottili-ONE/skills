#!/usr/bin/env python3
"""Self-test for check_rls_migration.py.

The checker is per-table and keyed on the accepted tenant GUC names, which are
configuration (`guc-names.json`), not a constant of the script (see
docs/truth/REPAIR_LOG.md, D-040). It must:
  * PASS the three real hq migrations (copies under tests/fixtures/hq-migrations),
  * FAIL the three hostile fixtures (no FORCE / no company_id / GRANT ALL),
  * PASS the skill's own good example (now written to the product standard),
  * FAIL the skill's own bad example,
  * honour every name in guc-names.json and reject a name nobody sets,
  * exit 2 on a missing file and on no args,
  * emit machine-readable --json.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECK = ROOT / "scripts" / "check_rls_migration.py"
EX = ROOT / "references" / "examples"

# The real hq-v2 migrations are copied into this repository as fixtures
# (tests/fixtures/hq-migrations, provenance in tests/fixtures/PROVENANCE.md).
# A committed test must not read a sibling repository, so the self-test uses the
# copies; when the skill is installed standalone they are absent and the
# self-test says so instead of failing on a foreign path.
REPO_ROOT = Path(__file__).resolve().parents[4]
HQ_FIXTURES = REPO_ROOT / "tests" / "fixtures" / "hq-migrations"

HOSTILE = [
    "hostile_1_no_force.sql",
    "hostile_2_no_company_id.sql",
    "hostile_3_grant_all.sql",
]


def run(*paths: str) -> tuple[int, str]:
    p = subprocess.run([sys.executable, str(CHECK), *paths],
                       capture_output=True, text=True, check=False)
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

    corpus = sorted(HQ_FIXTURES.glob("*.sql")) if HQ_FIXTURES.is_dir() else []
    if corpus:
        for m in corpus:
            rc, out = run(str(m))
            if rc != 0:
                failures.append(f"real hq migration {m} must exit 0, got {rc}\n{out}")
    else:
        absent = str(HQ_FIXTURES / "does-not-exist.sql")
        rc, out = run(absent)
        if rc != 2:
            failures.append(f"missing migration {absent} must exit 2, got {rc}\n{out}")
        elif "not found" not in out:
            failures.append(f"missing migration {absent} must report 'not found'\n{out}")
        print(
            f"note: the real hq fixtures ({HQ_FIXTURES}) are not installed; "
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
    summary = f"{len(corpus)} real hq PASS" if corpus else "missing-file contract"
    print(f"ok: pg-rls migration checker self-test ({summary}, 3 hostile FAIL)")
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


def test_every_configured_guc_name_passes() -> None:
    """A policy keyed on any accepted name is accepted, an unknown one is not."""
    config = json.loads((ROOT / "guc-names.json").read_text(encoding="utf-8"))
    names = [entry["name"] for entry in config["accepted_names"]]
    assert names, "guc-names.json must list at least one accepted name"
    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        for name in names:
            table = f"tenant_{name.replace('.', '_')}"
            sql = (
                f"CREATE TABLE {table} (id uuid PRIMARY KEY, company_id text NOT NULL);\n"
                f"CREATE POLICY {table}_tenant ON {table} USING "
                f"(company_id = current_setting('{name}', true));\n"
                f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;\n"
                f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY;\n"
            )
            path = t / f"{name}.sql"
            path.write_text(sql, encoding="utf-8")
            rc, out = run(str(path))
            assert rc == 0, f"{name} must be accepted, got {rc}: {out}"
        unknown = t / "unknown.sql"
        unknown.write_text(
            "CREATE TABLE tenant_unknown (id uuid PRIMARY KEY, company_id text NOT NULL);\n"
            "CREATE POLICY tenant_unknown_tenant ON tenant_unknown USING "
            "(company_id = current_setting('app.not_a_real_setting', true));\n"
            "ALTER TABLE tenant_unknown ENABLE ROW LEVEL SECURITY;\n"
            "ALTER TABLE tenant_unknown FORCE ROW LEVEL SECURITY;\n",
            encoding="utf-8",
        )
        rc, out = run(str(unknown))
        assert rc == 1, f"an unknown GUC must be rejected, got {rc}: {out}"
        assert "not keyed on an accepted tenant GUC" in out, out
    print("ok: every configured GUC name is accepted, an unknown one is not")


EDGE_TESTS = [
    ("json output", test_json_output),
    ("usage error", test_usage_error),
    ("configured GUC names", test_every_configured_guc_name_passes),
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
