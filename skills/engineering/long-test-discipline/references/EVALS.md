# Long Test Discipline — EVALS (verified 2026-10-07, host Biest)

Each prompt below includes expected behaviour and failure signs.

## 1. — Run a flaky test and report evidence
**Prompt**: "The test `tests/test_worker.py::test_long_task` flakes sometimes. Run it and tell me if it passes."
**Expected behaviour**: The skill triggers because the test is long-running or flaky. The agent runs it with the wrapper script, records the seed, re-runs on failure with `--lf`, and reports pass/fail with the log path and seed. The agent never uses `&` or `nohup`.
**Failure signs**: Agent runs with `&` and loses the log; agent says "it passed" without a log; no seed recorded; more than two reruns without root-cause fix.
**What the skill changes vs no skill**: without the skill an agent runs `pytest tests/test_worker.py::test_long_task` in the background, the shell exits, and the log is gone — the agent then reports "it passed" from memory. The skill makes the foreground wrapper with a recorded seed the only acceptable way to run, so a flake is a finding with a log path and a seed, not a shrug.

## 2. — A test timed out — what happened?
**Prompt**: "The CI job killed `tests/test_e2e.py` after 900 seconds. Inspect the log and tell me how far it got."
**Expected behaviour**: The agent inspects `$LOG` for partial output, looks for "Killed" or incomplete JSON lines, reports that timeout was too short or the test hung, and suggests a longer timeout or a fix to the hang. The agent does not assume success from partial output.
**Failure signs**: Agent says "it probably passed" based on partial output; agent does not inspect the log; agent suggests lowering the timeout instead of raising it or fixing the hang.
**What the skill changes vs no skill**: without the skill an agent reads the tail of a killed log and says "it probably passed". The skill makes the JSON summary record the pass/fail signal: a log that does not end in the summary is a kill, not a failure, and the timeout is raised or the hang is fixed instead of assumed away.

## 3. — Resource limit too tight on a shared host
**Prompt**: "Running `tests/test_worker.py` fails with `fork: retry: Resource temporarily unavailable`. The host is shared with other lanes."
**Expected behaviour**: The agent recognises the ulimit ceiling, raises `MAX_PROCS`/`MAX_VMEM_KB` env vars in the wrapper invocation, or splits the suite so fewer processes are spawned in one run. It never lowers the test's own resource use as a workaround.
**Failure signs**: Agent re-runs with `&` to dodge the error; agent edits the test to use fewer resources; agent ignores the error and reports "passed".
**What the skill changes vs no skill**: without the skill an agent re-runs with `&` to dodge the fork error or edits the test to use fewer resources. The skill makes raising `MAX_PROCS`/`MAX_VMEM_KB` (or splitting the suite) the response, so a shared-host resource ceiling is surfaced instead of masked.

## 4. — Worker process must survive the test
**Prompt**: "I need a background worker running while `tests/test_integration.py` runs. Set it up."
**Expected behaviour**: The agent starts the worker in the same foreground command chain (e.g. `run_long_test.sh` with a fixture that launches the worker, or a `&&`-chained script), never with `&`/`nohup`/`setsid`, and verifies the worker's output is captured in the same log.
**Failure signs**: Agent uses `&` and the worker dies when the shell exits; worker log is separate from test log; agent cannot prove the worker was alive during the test.
**What the skill changes vs no skill**: without the skill an agent starts the worker with `&` and it dies when the shell exits, so the integration test runs against a dead worker and passes for the wrong reason. The skill chains the worker into the same foreground command and captures its output in the same log, so the worker being alive is provable.

## 5. — CI must run a long test deterministically
**Prompt**: "Wire `tests/test_e2e.py` into CI so it runs on every PR."
**Expected behaviour**: The agent commits the wrapper script to `scripts/`, sets a timeout matching the CI job limit (never exceeding it), makes the log an artifact, and never hardcodes `&`. On flake it fails fast with evidence instead of silently rerunning until green.
**Failure signs**: CI script uses `&`; no log artifact; timeout exceeds CI job limit; agent retries until green without recording the seed.
**What the skill changes vs no skill**: without the skill an agent wires the test into CI with `&` and no artifact. The skill commits the wrapper to `scripts/`, sets a timeout under the CI job limit, makes the log an artifact, and fails fast on flake with evidence, so a CI run is reproducible and never silently rerun until green.

## 6. — Prove resource usage for a test
**Prompt**: "Give me the wall time, peak RSS, and process count for `tests/test_heavy.py`."
**Expected behaviour**: The agent runs the wrapper with `/usr/bin/time -v` (or pytest `--durations=5`), captures Max RSS from GNU time output, and reports wall time from the log's `WALL=` line plus the exit code.
**Failure signs**: agent reports only "it passed"; agent uses `&` and cannot time it; no evidence recorded; Max RSS not captured; no JSON record produced.
**What the skill changes vs no skill**: without the skill an agent reports "it passed" with no wall time, no RSS and no JSON. The skill makes `/usr/bin/time -v` Max RSS and the log's `WALL=` line the evidence, so resource usage is a recorded number rather than a feeling.

## Worked examples

**Good run** (foreground wrapper, seed recorded, JSON summary present):
```bash
SEED=12345 timeout 900 /usr/local/bin/heavy pytest tests/test_worker.py::test_long_task -p no:randomly --randomly-seed=12345 > /tmp/run.log 2>&1
tail -1 /tmp/run.log   # -> {"seed":12345,"wall":42,"exit":0,"max_rss_mb":310}
```
**Bad run** (background process, log lost):
```bash
pytest tests/test_worker.py &   # killed when the shell exits; no log, no exit code
```
**Good resource-cap invocation** (raises the ceiling, never weakens the test):
```bash
MAX_PROCS=64 MAX_VMEM_KB=67108864 /usr/local/bin/heavy pytest tests/test_worker.py
```
**Bad invocation** (lowers the ceiling and hides the real problem):
```bash
ulimit -u 8; pytest tests/test_worker.py   # masks the fork failure instead of fixing it
```

## Near-miss prompts (act before the incident)
- **N1 — "Just run it in the background."** Answer: no. Background processes are killed when the shell exits and the log never appears; use `run_long_test.sh` in the foreground so the log is captured and the exit code is checkable.
- **N2 — "It passed once, it'll pass again."** Answer: no. Re-run with a recorded seed; a single green run proves nothing about flake rate. Log the seed and the rerun count.
- **N3 — "The timeout is probably fine."** Answer: no. Check the log ends with the JSON summary record, not a partial line. A half-written log is a kill, not a failure.
- **N4 — "Lower the ulimit to make it fit."** Answer: no. Raise `MAX_PROCS`/`MAX_VMEM_KB` or split the suite; never weaken the test's own resource use.
- **N5 — "The CI job timed out, just lower the timeout."** Answer: no. Match the timeout to the CI job limit and fix the hang or split the test; never exceed the CI limit.
- **N6 — "The log is on my laptop, the CI can't read it."** Answer: no. Commit the log as an artifact or write it to the shared tree; a pointer that does not resolve on Biest is not evidence.
- **N7 — "The worker is background, it doesn't need to be in the log."** Answer: no. A background worker dies when the shell exits and its output is lost; chain it in the same foreground command and capture its output in the same log.
