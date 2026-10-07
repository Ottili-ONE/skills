# Long Test Discipline — Full Procedure (verified 2026-10-07)

## 1. Classify the test by duration and resource need
- **Unit**: < 60 s, no external services. Run directly with pytest or equivalent.
- **Integration**: 1-15 min, needs a DB or worker. Use the wrapper script below.
- **End-to-end**: > 15 min, needs a full stack. Use the wrapper script with higher limits; run on demand only.

## 2. The wrapper script (`scripts/run_long_test.sh`)
```bash
#!/bin/bash
set -euo pipefail
TEST_NAME="${1:?usage: run_long_test.sh <test_name>}"
LOG="logs/${TEST_NAME}.log"
mkdir -p logs
# Resource limits
ulimit -v $((4 * 1024 * 1024))
ulimit -u 8
# Timeout: 900 s = 15 min
timeout 900 /usr/local/bin/heavy pytest "$TEST_NAME"   --randomly-seed "${SEED:-42}"   --tb=short   > "$LOG" 2>&1
EXIT=$?
echo "EXIT=$EXIT LOG=$LOG"
exit $EXIT
```
Run it in the foreground: `bash scripts/run_long_test.sh tests/test_worker.py`.
Never append `&`, `nohup`, or `setsid`.

## 3. Flake handling
If a test fails, re-run with the same seed and order:
```bash
SEED=$(grep "randomly-seed" "$LOG" | awk '{print $NF}')
timeout 900 /usr/local/bin/heavy pytest "$TEST_NAME" --randomly-seed "$SEED" --lf > "${LOG}.rerun" 2>&1
```
If it passes on rerun, record the seed and investigate ordering dependency.
If it fails again, it is a real failure — do not retry more than twice without fixing the root cause.

## 4. Resource monitoring
Add `--durations=5` to pytest to get slowest tests; add `-s` only when you need live stdout (it mixes with log capture).
For memory profiling, use `/usr/bin/time -v` before the command and capture Max RSS from its output.
For CPU profiling, use `perf stat` if available on Biest; otherwise rely on wall time + exit code as evidence.

## 5. CI integration
In CI, use the same wrapper script but set timeout to match your CI job limit (e.g., timeout=600 for a CI job of 660 s).
Never hardcode `&` in CI scripts; they run non-interactively and kill background processes at job end.
Do not retry background variants — if a test flakes in CI, fail fast and report evidence instead of silently rerunning until green.
The log path must be an artifact so reviewers can inspect it after the job ends.

## 6. Recovery from a killed test
If timeout kills a test, inspect `` for partial output; look for "Killed", "Timeout", or incomplete JSON lines.
A half-written log that ends mid-line is expected — treat it as evidence that timeout was too short or the test hung.
Do not assume success from partial output; re-run with a longer timeout if needed.
Record whether the hang was deterministic (same seed reproduces) or random (different seed changes behavior).
