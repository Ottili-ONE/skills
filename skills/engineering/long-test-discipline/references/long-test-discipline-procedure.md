# Long Test Discipline — Full Procedure (verified 2026-10-07, host Biest)

## Verified tool versions
- pytest >= 8.x: `--randomly-seed`, `--lf`, `--durations`, `--tb=short` confirmed present on Biest 2026-10-07.
- GNU coreutils `timeout`: exit code 124 on timeout, 137 on SIGKILL; verified on Biest 2026-10-07.
- bash `ulimit`: `-v` virtual-memory in KiB; `-u` max user processes; verified on Biest 2026-10-07.
- `/usr/local/bin/heavy`: foreground wrapper used by all Ottili long tests; verified present on Biest 2026-10-07.

## 1. Classify the test by duration and resource need
| Class | Duration | External services? | Wrapper | Limits |
|-------|----------|--------------------|---------|--------|
| unit | < 60 s | no | direct pytest | none needed |
| integration | 1-15 min | DB / worker likely | run_long_test.sh | ulimit -v 8GiB -u 64; timeout 900s |
| end-to-end | > 15 min | full stack required | run_long_test.sh + raise limits or split test | ulimit -v adjustable via MAX_VMEM_KB env; timeout adjustable via CI job limit; never exceed host cgroup ceiling (check `cat /sys/fs/cgroup/pids.max` if available) — threshold: if test needs >3x CI job limit, split into smaller tests instead of raising timeout indefinitely [long-test discipline](references/SOURCES.md#primary-sources) [pytest docs](references/SOURCES.md#primary-sources)

### Worked example — good output
```bash
$ bash scripts/run_long_test.sh tests/test_worker.py
EXIT=0 LOG=logs/tests/test_worker.py.log SEED=42 WALL=...
$ tail -3 logs/tests/test_worker.py.log
======================= short test summary info =======================
PASSED tests/test_worker.py::test_long_task
PASSED tests/test_worker.py::test_retry
======================= short test summary info =======================
EXIT=0 LOG=logs/tests/test_worker.py.log SEED=42 WALL=...
```

### Worked example — bad output
```bash
$ bash scripts/run_long_test.sh tests/test_worker.sh: fork: retry: Resource temporarily unavailable
EXIT=? LOG missing or empty
```
Root cause: ulimit -u too low for pytest fork model or container PID ceiling hit; fix by raising MAX_PROCS env var or splitting the test suite so fewer processes are spawned in one run [long-test discipline](references/SOURCES.md#primary-sources).

### Worked example — flake detection
```bash
# first run fails
$ bash scripts/run_long_test.sh tests/test_flaky.py
EXIT=1 LOG=logs/tests/test_flaky.py.log
# rerun with recorded seed
$ SEED=$(grep "SEED=" logs/tests/test_flaky.py.log | tail -1 | sed "s/.*SEED=//")
$ timeout 900 /usr/local/bin/heavy pytest tests/test_flaky.py --randomly-seed "$SEED" --lf > logs/tests/test_flaky.py.rerun.log 2>&1
# if rerun passes -> ordering dependency recorded in EVALS evidence file
# if rerun fails -> real failure, stop after max two reruns [pytest docs](references/SOURCES.md#primary-sources)
```

### Worked example — timeout kill inspection
```bash
$ grep -E "Killed|Timeout" logs/tests/test_e2e.log || echo "no kill marker found"
# partial JSON at end of log = hung test => raise timeout or fix hang [timeout docs](references/SOURCES.md#primary-sources)
```

## Recovery from a killed test
If timeout kills a test, inspect log for partial output; look for "Killed", "Timeout", or incomplete JSON lines. A half-written log that ends mid-line is expected — treat it as evidence that timeout was too short or the test hung. Do not assume success from partial output; re-run with a longer timeout if needed. Record whether the hang was deterministic (same seed reproduces) or random (different seed changes behavior).
