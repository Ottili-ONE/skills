# Incidents — verifiable-environments

Real verifier failures, the observable signature that exposes them, and the
exact recovery procedure. Each incident is a case a generic agent gets wrong
because it wrote checks that check the happy path.

## I1 — Verifier that imports the environment module

- **What happened**: a harness imported `from environment import run_checks` so
  it could reuse the environment's own assertions. The environment had a bug
  that let a broken agent pass. The verifier shared the bug and reported the
  broken agent as good.
- **Observable signature**: the verifier's source imports a module from the
  environment under test; the checks file lives inside the agent's write
  scope.
- **Recovery**: write the verifier against a `SPEC.md` the agent cannot edit.
  The spec is a document, not code; the verifier reads the spec and the agent's
  output, never the environment's internals.
- **Prevention**: the spec/implementation split is step 1 of the procedure.

## I2 — A decorative check that passes on a broken agent

- **What happened**: the only check was "did the agent finish?". The broken
  agent finished (it exited 0 having done nothing) and the lazy agent finished
  (it wrote an empty file). Every agent scored 100%.
- **Observable signature**: `pass_good == pass_broken == pass_lazy == 1.0`;
  discriminating power 0.00 against the 0.30 floor.
- **Recovery**: rewrite every check as an observable outcome the broken agent
  cannot reach without the intended work. Add the rule-of-two: every check
  needs a second independent defence.
- **Prevention**: `scripts/verify_harness.py` reports `power(broken)` and
  `power(lazy)` and exits 1 below the floor.

## I3 — Pass rate 100% on every agent

- **What happened**: a harness with three trivially-satisfied checks scored every
  agent at 1.0. The team read the perfect scores as "the harness is strict".
- **Observable signature**: `pass_good == 1.0` and `pass_lazy == 1.0`; the
  known-good agent passes at 100% but so does the lazy agent.
- **Recovery**: require `pass_good >= 0.80` AND `pass_good - pass_lazy >= 0.30`
  AND `pass_good - pass_broken >= 0.30`. A harness that scores everyone 100% has
  no discriminating power and must be redesigned.
- **Prevention**: the harness exits 1 when discriminating power is below the
  floor; it does not report a misleading PASS.

## I4 — Sandbox contract not pinned

- **What happened**: the harness let the agent choose its own tools mid-run.
  The agent `curl`ed an internal service that held the answer and scored 100%
  without doing the work.
- **Observable signature**: the contract JSON is absent, or `network` is not
  `deny`, or `filesystem` is not `scoped`, or `exec` is not allowlisted.
- **Recovery**: pin the contract before any agent runs and assert it. A
  contract with `network: allow` or `filesystem: open` fails the whole harness.
- **Prevention**: `assert_contract()` runs before any agent output is read and
  its failures are reported before the pass-rate computation.

## I5 — A check that depends on wall-clock time

- **What happened**: a check required the agent to finish within 30 seconds.
  On a slow CI box the known-good agent timed out and scored 0%, so the harness
  was "too strict" and was relaxed until it accepted a 60-second lazy agent.
- **Observable signature**: a check whose pass condition involves a timestamp,
  a duration, or `time.time()`.
- **Recovery**: replace time with a deterministic completion signal (a file at
  a path, an exit code, a content match). Time-based checks are flaky and
  gameable: an agent that stalls to the timeout scores 100% on a "did it
  finish" check.
- **Prevention**: the verification checklist requires "no check depends on
  wall-clock time".

## I6 — Harness exits 0 after a check is neutered

- **What happened**: the team flipped one check to always-pass to test the
  harness and it still exited 0. The check had no power to begin with, and the
  harness could not detect a dead check.
- **Observable signature**: `--neutered-checks` supplied, power unchanged, exit 0.
- **Recovery**: flip the check that separates the lazy agent from the good
  agent. If power still does not drop, that check is not load-bearing — find
  another one and repeat. Neutering exactly one check is the smallest mutation
  that must be caught.
- **Prevention**: `verify_harness.py --neutered-checks` re-runs the live
  harness against the neutered checks and exits 1 unless power dropped.
