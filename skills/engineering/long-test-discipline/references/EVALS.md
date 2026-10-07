# Long Test Discipline — EVALS (verified 2026-10-07)

## Prompt 1: Run a flaky test and report evidence
**Prompt**: "The test `tests/test_worker.py::test_long_task` flakes sometimes. Run it and tell me if it passes."
**Expected behaviour**: The skill triggers because the test is long-running or flaky. The agent runs it with the wrapper script, records the seed, re-runs on failure with `--lf`, and reports pass/fail with the log path and seed. The agent never uses `&` or `nohup`.
**Failure signs**: Agent runs with `&` and loses the log; agent says "it passed" without a log; no seed recorded; more than two reruns without root-cause fix.

## Prompt 2: A test timed out — what happened?
**Prompt**: "The CI job killed `tests/test_e2e.py` after 900 seconds. Inspect the log and tell me how far it got."
**Expected behaviour**: The agent inspects `$LOG` for partial output, looks for "Killed" or incomplete JSON lines, reports that timeout was too short or the test hung, and suggests a longer timeout or a fix to the hang. The agent does not assume success from partial output.
**Failure signs**: Agent says "it probably passed" based on partial output; agent does not inspect the log; agent suggests lowering the timeout instead of raising it or fixing the hang.
