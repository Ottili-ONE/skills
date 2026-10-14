#!/usr/bin/env python3
"""Self-test for check_problem_catalogue.py.

Covers the fixture set named in the DESIGN: good (1), the six bad cases, and the
malformed (duplicate-key) catalogue. Exit 0 only when every fixture behaves as
documented: good is clean, each bad case fails with its specific defect, and the
malformed catalogue is rejected before any YAML is parsed.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECK = ROOT / "scripts" / "check_problem_catalogue.py"
EX = ROOT / "references" / "examples"
BAD = EX / "bad"


def run(*args: str) -> tuple[int, str]:
    p = subprocess.run([sys.executable, str(CHECK), *args],
                       capture_output=True, text=True)
    return p.returncode, (p.stdout + p.stderr)


def main() -> int:
    failures = []

    # 1. good example must be clean.
    good, out = run(
        "--catalogue", str(EX / "good" / "catalogue.json"),
        "--openapi", str(EX / "good" / "openapi.yaml"),
        "--schema-dir", str(EX / "good" / "schemas"))
    if good != 0:
        failures.append(f"good example must exit 0, got {good}\n{out}")

    # 2. six bad cases, each failing with its specific defect.
    expected = {
        "duplicate_code": ("1", "duplicate code"),
        "missing_openapi_response": ("1", "no OpenAPI response entry"),
        "missing_problem_json": ("1", "missing application/problem+json"),
        "retryable_without_retry_after": ("1", "no retry_after"),
        "missing_schema_file": ("1", "no schema file"),
        "example_fails_schema": ("1", "longer than maxLength 500"),
    }
    for name, (code, needle) in expected.items():
        d = BAD / name
        if (d / "schemas").is_dir():
            c, out = run("--catalogue", str(d / "catalogue.json"),
                         "--openapi", str(d / "openapi.yaml"),
                         "--schema-dir", str(d / "schemas"))
        else:
            c, out = run("--catalogue", str(d / "catalogue.json"),
                         "--openapi", str(d / "openapi.yaml"))
        if c != int(code) or needle not in out:
            failures.append(f"{name}: expected exit {code} containing {needle!r}, got {c}\n{out}")

    # 3. malformed fixture: duplicate code keys must be rejected (exit 1) before YAML
    #    parsing, because yaml.safe_load would silently keep the last value. The
    #    duplicate_code fixture carries the same code twice and is the malformed case.
    c, out = run("--catalogue", str(BAD / "duplicate_code" / "catalogue.json"),
                 "--openapi", str(EX / "good" / "openapi.yaml"))
    if c != 1 or "duplicate code" not in out:
        failures.append(f"malformed duplicate_code catalogue must exit 1 with 'duplicate code', got {c}\n{out}")

    # 4. truly missing files are malformed input (exit 2), not drift.
    c, out = run("--catalogue", "does-not-exist.yaml", "--openapi", "nope.yaml")
    if c != 2:
        failures.append(f"malformed input must exit 2, got {c}\n{out}")

    if failures:
        for f in failures:
            print(f"FAIL: {f}", file=sys.stderr)
        return 1
    print("ok: problem-json catalogue checker self-test (1 good, 6 bad, 1 malformed)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
