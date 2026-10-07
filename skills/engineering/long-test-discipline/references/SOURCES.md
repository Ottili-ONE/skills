# Long Test Discipline — SOURCES (verified 2026-10-07, host Biest)

## Primary sources
- pytest documentation: https://docs.pytest.org/en/stable/ — verified 2026-10-07; pytest 8.x API for `--randomly-seed`, `--lf`, `--durations`. Version-sensitive: re-verify when pytest releases a new major.
- GNU coreutils `timeout`: https://www.gnu.org/software/coreutils/manual/html_node/timeout-invocation.html — verified 2026-10-07; exit codes 124 (timeout) and 137 (SIGKILL). Version-sensitive: re-verify on coreutils release.
- bash `ulimit`: https://www.gnu.org/software/bash/manual/html_node/The-Shopt-Builtin.html — verified 2026-10-07; `-v` (virtual memory in KiB) and `-u` (max user processes). Stable.
- `/usr/bin/time -v` (GNU time): https://www.gnu.org/software/time/manual/html_node/Invoking-time.html — verified 2026-10-07 on Biest host; Max RSS field. Version-sensitive: field name stable across GNU time releases.
- `/usr/local/bin/heavy`: Ottili foreground test wrapper; verified present on Biest 2026-10-07.

## Conflicts between sources
- pytest-randomly vs fixed order: pytest-randomly seeds tests per run; some teams prefer deterministic order. Resolution: default seed 42, record seed in log, re-run with `--lf` on flake. See references/long-test-discipline-procedure.md section "Flake handling".
- `ulimit -u` too low vs shared-host fairness: a tight `-u` protects the host but breaks pytest's fork model. Resolution: default 64 processes, override via `MAX_PROCS` env var; never below the number of workers the test needs. See references/long-test-discipline-procedure.md section "Resource limits".
