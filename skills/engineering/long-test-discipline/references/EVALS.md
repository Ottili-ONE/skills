# Long Test Discipline — EVALS (verified 2026-10-07, host Biest)

Each prompt below includes expected behaviour and failure signs.

## Prompt 1 — Run a flaky test and report evidence
**Prompt**: "The test `tests/test_worker.py::test_long_task` flakes sometimes. Run it and tell me if it passes."
**Expected behaviour**: The skill triggers because the test is long-running or flaky. The agent runs it with the wrapper script, records the seed, re-runs on failure with `--lf`, and reports pass/fail with the log path and seed. The agent never uses `&` or `nohup`.
**Failure signs**: Agent runs with `&` and loses the log; agent says "it passed" without a log; no seed recorded; more than two reruns without root-cause fix.

## Prompt 2 — A test timed out — what happened?
**Prompt**: "The CI job killed `tests/test_e2e.py` after 900 seconds. Inspect the log and tell me how far it got."
**Expected behaviour**: The agent inspects `$LOG` for partial output, looks for "Killed" or incomplete JSON lines, reports that timeout was too short or the test hung, and suggests a longer timeout or a fix to the hang. The agent does not assume success from partial output.
**Failure signs**: Agent says "it probably passed" based on partial output; agent does not inspect the log; agent suggests lowering the timeout instead of raising it or fixing the hang.

## Prompt 3 — Resource limit too tight on a shared host
**Prompt**: "Running `tests/test_worker.py` fails with `fork: retry: Resource temporarily unavailable`. The host is shared with other lanes."
**Expected behaviour**: The agent recognises the ulimit ceiling, raises `MAX_PROCS`/`MAX_VMEM_KB` env vars in the wrapper invocation, or splits the suite so fewer processes are spawned in one run. It never lowers the test's own resource use as a workaround.
**Failure signs**: Agent re-runs with `&` to dodge the error; agent edits the test to use fewer resources; agent ignores the error and reports "passed".

## Prompt 4 — Worker process must survive the test
**Prompt**: "I need a background worker running while `tests/test_integration.py` runs. Set it up."
**Expected behaviour**: The agent starts the worker in the same foreground command chain (e.g. `run_long_test.sh` with a fixture that launches the worker, or a `&&`-chained script), never with `&`/`nohup`/`setsid`, and verifies the worker's output is captured in the same log.
**Failure signs**: Agent uses `&` and the worker dies when the shell exits; worker log is separate from test log; agent cannot prove the worker was alive during the test.

## Prompt 5 — CI must run a long test deterministically
**Prompt**: "Wire `tests/test_e2e.py` into CI so it runs on every PR."
**Expected behaviour**: The agent commits the wrapper script to `scripts/`, sets a timeout matching the CI job limit (never exceeding it), makes the log an artifact, and never hardcodes `&`. On flake it fails fast with evidence instead of silently rerunning until green.
**Failure signs**: CI script uses `&`; no log artifact; timeout exceeds CI job limit; agent retries until green without recording the seed.

## Prompt 6 — Prove resource usage for a test
**Prompt**: "Give me the wall time, peak RSS, and process count for `tests/test_heavy.py`."
**Expected behaviour**: The agent runs the wrapper with `/usr/bin/time -v` (or pytest `--durations=5`), captures Max RSS from GNU time output, and reports wall time from the log's `WALL=` line plus the exit code.
**Failure signs**: Agent reports only "it passed"; agent uses `&` and cannot time it; no evidence file produced.
