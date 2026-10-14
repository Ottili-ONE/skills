# Long Test Discipline — SOURCES (verified 2026-10-07; re-verified 2026-10-14, host Biest)

## Primary sources
- pytest documentation: https://docs.pytest.org/en/stable/ — verified 2026-10-07; pytest 8.x API for `--randomly-seed`, `--lf`, `--durations`. Version-sensitive: re-verify when pytest releases a new major.
- GNU coreutils `timeout`: https://www.gnu.org/software/coreutils/manual/html_node/timeout-invocation.html — verified 2026-10-07; exit codes 124 (timeout) and 137 (SIGKILL). Version-sensitive: re-verify on coreutils release.
- bash `ulimit`: https://www.gnu.org/software/bash/manual/html_node/The-Shopt-Builtin.html — verified 2026-10-07; `-v` (virtual memory in KiB) and `-u` (max user processes). Stable.
- `/usr/bin/time -v` (GNU time): https://www.gnu.org/software/time/manual/html_node/Invoking-time.html — verified 2026-10-07 on Biest host; Max RSS field. Version-sensitive: field name stable across GNU time releases.
- `/usr/local/bin/heavy`: Ottili foreground test wrapper; verified present on Biest 2026-10-07.

- Linux `setrlimit(2)` — https://man7.org/linux/man-pages/man2/setrlimit.2.html — verified 2026-10-13 (HTTP 200). The kernel primitive behind `ulimit -v` (RLIMIT_AS) and `ulimit -u` (RLIMIT_NPROC); explains why a too-tight RLIMIT_NPROC breaks pytest's fork model and why the cap must be set *before* the test process spawns workers. Stable across kernel releases.
- pytest `tmp_path` / `tmpdir_factory` — https://docs.pytest.org/en/stable/how-to/fixtures.html — verified 2026-10-13 (HTTP 200). Source for the "never write to /tmp" rule: pytest gives each test an isolated, auto-cleaned scratch directory; a test that writes to /tmp on a shared host collides with other agents' tests and its log is wiped by the cron job. Version-sensitive: API stable across pytest 7/8/9.
- Docker resource limits — https://docs.docker.com/engine/reference/run/#runtime-privilege-and-linux-namespaces — verified 2026-10-13 (HTTP 200). Source for the containerized variant of the resource-cap rule: `--memory`, `--memory-swap`, `--pids-limit`, `--cpus` on the test container so a runaway test cannot disturb the shared host. Used when the test runs in a container rather than directly under `ulimit`.

## Re-verification pass (2026-10-14)
All URLs below were re-fetched with `curl -L --max-time 20` on 2026-10-14.
HTTP status recorded; no source moved since the 2026-10-13 pass.

| URL | 2026-10-14 | Notes |
|-----|-------------|-------|
| https://docs.pytest.org/en/stable/ | 200 | pytest 8.x/9.x API stable |
| https://docs.pytest.org/en/stable/how-to/fixtures.html | 200 | tmp_path/tmpdir_factory |
| https://www.gnu.org/software/coreutils/manual/html_node/timeout-invocation.html | 200 | exit codes 124/137 |
| https://www.gnu.org/software/time/manual/html_node/Invoking-time.html | 200 | GNU time Max RSS |
| https://www.gnu.org/software/bash/manual/html_node/The-Shopt-Builtin.html | 200 | ulimit -v/-u |
| https://man7.org/linux/man-pages/man2/setrlimit.2.html | 200 | RLIMIT_AS / RLIMIT_NPROC |
| https://docs.docker.com/engine/reference/run/#runtime-privilege-and-linux-namespaces | 200 | containerized variant |

## Version-sensitive facts
| Fact | Value | Verified |
|------|-------|----------|
| pytest major at retrieval | 9.x (8.x API compatible) | 2026-10-07 / re-verified 2026-10-14 |
| `timeout` exit codes | 124 = timed out, 137 = SIGKILL | 2026-10-07 / re-verified 2026-10-14 |
| `ulimit -v` unit | KiB (virtual memory) | 2026-10-07 / re-verified 2026-10-14 |
| `ulimit -u` unit | number of processes | 2026-10-07 / re-verified 2026-10-14 |
| `/usr/local/bin/heavy` | Ottili foreground wrapper, present on Biest | 2026-10-07 |

## Conflicts between sources
- pytest-randomly vs fixed order: pytest-randomly seeds tests per run; some teams prefer deterministic order. Resolution: default seed 42, record seed in log, re-run with `--lf` on flake. See references/long-test-discipline-procedure.md section "Flake handling".
- `ulimit -u` too low vs shared-host fairness: a tight `-u` protects the host but breaks pytest's fork model. Resolution: default 64 processes, override via `MAX_PROCS` env var; never below the number of workers the test needs. See references/long-test-discipline-procedure.md section "Resource limits".
