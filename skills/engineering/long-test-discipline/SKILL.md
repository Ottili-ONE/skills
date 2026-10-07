---
name: long-test-discipline
description: "Runs long-running tests on a shared host: schedules them in the foreground with timeout wrappers, captures structured logs, enforces resource limits, handles flakes with deterministic reruns, and reports pass/fail with evidence. Use when a test takes minutes, needs a background worker, or fails intermittently."
license: MIT-compat
compatibility: "framework-agnostic; Linux host; pytest; shell; Ottili Biest host"
metadata: {}
allowed-tools: []
---
# Long Test Discipline Skill — Quick Reference (body <500 lines; full procedure in references/long-test-discipline-procedure.md)

## When to use this skill (trigger)
- A test takes more than ~60 seconds or needs a worker process.
- You are asked to run something "in the background" on a shared host.
- A test flakes: passes alone, fails in a suite, or fails only on the second run.
- You need to prove resource usage (CPU, memory, wall time) for a test.
- A timeout killed your test and you need to know how far it got.

## When NOT to use this skill
- Unit tests that finish in under a minute.
- Tests that require a live human operator.
- Tests that depend on network access that is not available on the host.

## Decision table — execution strategy
| Situation | Strategy | Pitfall |
|-----------|----------|---------|
| Test takes 2-15 min | `timeout 900 /usr/local/bin/heavy <cmd> > <log> 2>&1; tail -40 <log>` | Running with `&` loses the log when the shell exits |
| Test flakes | Re-run deterministically: same seed, same order, same env | Re-running "as-is" may hide the real cause |
| Test needs a worker | Start the worker in the same foreground command chain; never `&` | A detached worker is killed when the command returns |
| Resource limit needed | Wrap with `ulimit -v` (memory) and `timeout` (wall clock) | `ulimit` is per-shell; set it in the same command that runs the test |
| Test must run in CI | Use the same wrapper script; CI has no interactive shell | Hardcoding `&` works locally but dies in CI |

## Numbered procedure (summary; full recipe in references/long-test-discipline-procedure.md)
1. **Classify the test** — unit (<1 min), integration (1-15 min), or end-to-end (>15 min). Pick the wrapper accordingly.
2. **Write the wrapper** — a small shell script that sets `ulimit`, `timeout`, redirects output to a log, and runs the test. Commit it to `scripts/`.
3. **Run in the foreground** — never use `&`, `nohup`, or `setsid`. Use `timeout` so the command always returns.
4. **Capture evidence** — the log file plus a one-line summary (exit code, wall time, peak RSS).
5. **Handle flakes** — if the test fails, re-run with `--randomly-seed` (if pytest-randomly) or a fixed order; record the seed.
6. **Enforce resource limits** — set `ulimit -v` (virtual memory) and `ulimit -u` (processes) before the test.
7. **Report** — pass/fail with the log path, the seed, and the resource numbers.

## Pitfalls from research (real incidents)
- `&`-backgrounded processes are killed when the launching shell exits; the log never appears.
- A flaky test that passes on rerun hides a real ordering or resource problem.
- `ulimit` set in one command does not apply to a later command; it must wrap the test.
- A timeout that is too short leaves a half-written log that looks like a failure but is just a kill.
- Running the whole suite to "see if it still flakes" burns minutes and gives no evidence.

## Verification checklist (all must pass before you finish)
- [ ] The test runs in the foreground with a `timeout` wrapper.
- [ ] A log file is produced and contains the final summary line.
- [ ] Resource limits (`ulimit`) are set in the same command that runs the test.
- [ ] Flake reruns use a recorded seed and order.
- [ ] The wrapper script is committed to `scripts/` and is deterministic.
