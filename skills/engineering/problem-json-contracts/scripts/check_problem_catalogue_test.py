#!/usr/bin/env python3
"""Self-test for check_problem_catalogue.py: good example is clean, every bad example fails."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECK = ROOT / "scripts" / "check_problem_catalogue.py"
EX = ROOT / "references" / "examples"


def run(*args: str) -> tuple[int, str]:
    p = subprocess.run(
        [sys.executable, str(CHECK), *args],
        capture_output=True, text=True)
    return p.returncode, (p.stdout + p.stderr)


def main() -> int:
    failures = []
    good, out = run(
        "--catalogue", str(EX / "catalogue.json"),
        "--openapi", str(EX / "openapi.yaml"),
        "--schema-dir", str(EX / "schemas"))
    if good != 0:
        failures.append(f"good example must exit 0, got {good}\n{out}")

    expected = {
        "duplicate": "duplicate",
        "missing-response": "no OpenAPI response entry",
        "no-problem-content": "missing application/problem+json",
        "retryable-no-delay": "no retry_after",
    }
    for name, needle in expected.items():
        code, out = run(
            "--catalogue", str(EX / "bad" / name / "catalogue.json"),
            "--openapi", str(EX / "bad" / name / "openapi.yaml"))
        if code != 1 or needle not in out:
            failures.append(f"{name}: expected exit 1 containing {needle!r}, got {code}\n{out}")

    code, out = run("--catalogue", "does-not-exist.yaml", "--openapi", "nope.yaml")
    if code != 2:
        failures.append(f"malformed input must exit 2, got {code}\n{out}")

    if failures:
        for f in failures:
            print(f"FAIL: {f}", file=sys.stderr)
        return 1
    print("ok: problem-json catalogue checker self-test (4 good, 4 bad, 1 malformed)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
