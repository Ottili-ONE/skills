# DESIGN — long-test-discipline

## Trigger description (draft)
Fires when: a test takes more than ~60 seconds, must run in the background, or consumes enough
resources to disturb a shared host; when a test flakes; when an agent is tempted to use `&`,
`nohup`, or `setsid`; or when a timeout or resource cap must be chosen. Does NOT fire for:
fast unit tests that complete in seconds under default pytest.

## What it does better than existing public skills
pytest docs and GNU coreutils manuals document the *tools*; they do not document the shared-host
constraint. This skill fixes the concrete defaults: run through `/usr/local/bin/heavy`, cap with
`timeout`, log to a file in scratch, pin `ulimit -v`/`-u`, detect flakes with a fixed seed and
`--lf`, and never use background-process escapes (they are killed when the command returns and
the log never appears). It also defines the flake threshold: a test that passes twice in a row
after a failure is not fixed — the failure must be reproduced under the fixed seed first.

## Procedure outline
1. Estimate runtime; anything >60s goes through the heavy wrapper with a timeout 1.5x the estimate.
2. Set resource caps: `ulimit -v` for virtual memory, `ulimit -u` for user processes (default 64,
   override via MAX_PROCS, never below the worker count).
3. Log everything: `timeout 900 /usr/local/bin/heavy <cmd> > <log> 2>&1; tail -40 <log>`.
4. On flake: re-run with the recorded seed (`pytest --randomly-seed=<n>`), reproduce, then fix the
   test or the ordering — never silence.
5. Record the timeout, the seed, the resource caps, and the exit code in STATUS.md evidence.

## Scripts planned
- `scripts/run_long_test.sh` — wraps a command with timeout, ulimits, heavy, and log rotation.

## Five eval prompts
1. "Run the integration suite in the background." → agent must refuse `&`/`nohup` and use the
   foreground heavy+timeout+log pattern.
2. "The test flakes 1 in 20 runs." → agent must reproduce under the recorded seed, then fix or
   mark BLOCKED with the seed — never ignore.
3. "What timeout should I use for a 3-minute test?" → 270s (1.5x), recorded in the log.
4. "ulimit -u 64 breaks pytest's fork model." → agent raises MAX_PROCS to the worker count and
   documents the override.
5. "The log was wiped by a cron job." → agent must route logs to scratch (`../../scratch/...`),
   never /tmp.
