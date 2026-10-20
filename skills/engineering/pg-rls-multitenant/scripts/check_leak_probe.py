#!/usr/bin/env python3
"""Decide PASS or FAIL from the output of the RLS leak-test probe.

The probe runs as the application role and prints one measurement per line:

    a_sees_own<TAB>1
    a_sees_b<TAB>0
    unset_sees_rows<TAB>0

``a_sees_own`` is the number of rows tenant A may see (it seeded exactly
one), ``a_sees_b`` is the number of rows of tenant B that tenant A may see
and ``unset_sees_rows`` is the number of rows anybody may see while the
session carries no tenant. A leak test passes when the three numbers are 1, 0
and 0.

A measurement that is missing is a failure, not a zero: the probe did not run,
and a probe that did not run proves nothing.

The judgement lives in the ``ottili_rls`` package next to this file: this
script is the adapter that reads the captured output and returns an exit code.

Usage: check_leak_probe.py <probe-output-file>
Exit 0 = PASS, 1 = FAIL, 2 = usage error.
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from ottili_rls.leak import judge_probe_output
from ottili_rls.logging import configure_logging, log_event, new_run_id


def main() -> int:
    """Judge the probe output named on the command line."""
    ap = argparse.ArgumentParser(description="Judge the output of an RLS leak probe.")
    ap.add_argument("output", help="file with the captured probe output")
    ap.add_argument(
        "--log-level",
        default="WARNING",
        help="level of the structured run log (default WARNING)",
    )
    args = ap.parse_args()

    logger = configure_logging(args.log_level)
    run_id = new_run_id()
    path = Path(args.output)
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError as exc:
        print(f"FAIL: cannot read the probe output {path}: {exc}", file=sys.stderr)
        return 2

    verdict = judge_probe_output(text)
    log_event(
        logger,
        logging.INFO,
        "probe judged",
        run_id,
        file=str(path),
        passed=verdict.passed,
        measurements=len(verdict.measurements),
    )
    if verdict.passed:
        print("PASS: RLS leak test green")
        return 0
    print(f"FAIL: RLS leak test - block merge ({path})", file=sys.stderr)
    for finding in verdict.findings:
        print(f"  - {finding}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
