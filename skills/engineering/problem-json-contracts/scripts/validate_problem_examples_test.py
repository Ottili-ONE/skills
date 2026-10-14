#!/usr/bin/env python3
"""Self-test for scripts/validate_problem_examples.py.

Runs the validator against the good example set (must be OK) and against the
deliberately broken bad-example set (must report findings). Exit 0 on success.
"""
import subprocess, sys, os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SCRIPT = os.path.join(HERE, "validate_problem_examples.py")


def run(schema_dir, catalogue):
    cmd = [sys.executable, SCRIPT, "--schema-dir", schema_dir, "--catalogue", catalogue]
    return subprocess.run(cmd, capture_output=True, text=True)


def main():
    good = run(os.path.join(ROOT, "references", "examples", "schemas"),
               os.path.join(ROOT, "references", "examples", "catalogue.json"))
    if good.returncode != 0:
        print("FAIL: good examples should validate")
        print(good.stdout, good.stderr)
        return 1
    if "OK:" not in good.stdout:
        print("FAIL: good examples missing OK line:", good.stdout)
        return 1

    bad = run(os.path.join(ROOT, "references", "examples", "bad", "bad-example", "schemas"),
              os.path.join(ROOT, "references", "examples", "bad", "bad-example", "catalogue.json"))
    if bad.returncode != 1:
        print("FAIL: bad examples should report findings, got", bad.returncode)
        print(bad.stdout, bad.stderr)
        return 1
    if "FINDINGS:" not in bad.stdout:
        print("FAIL: bad examples missing FINDINGS line:", bad.stdout)
        return 1

    print("ok: RFC 9457 example validator self-test (good=OK, bad=FINDINGS)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
