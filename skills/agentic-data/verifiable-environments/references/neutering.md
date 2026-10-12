# Verify the verifier (neutering) — verifiable-environments

A harness that cannot detect a dead check is decoration with a report. This page
records the one-step proof that the verifier is itself verified.

## The test
1. Run the harness on good/broken/lazy. Record `power_vs_lazy` and `power_vs_broken`.
2. Flip **exactly one** check to always-pass (it asserts a condition that is false
   for every agent, e.g. a marker file no agent creates, with `exists: false`).
3. Re-run the harness on the same three agents with the neutered checks.
4. The power must drop. If it does not, the harness cannot detect a dead check and
   is not verified.

## Why exactly one check
Flipping *all* checks proves nothing: every harness collapses. Flipping *none*
proves nothing either. One check is the smallest mutation that must be caught,
and it isolates which check carries which power.

## What "always-pass" means in the fixture
```json
{"name": "summary_file_neutered", "path": "__neutered_marker__", "exists": false}
```
This passes for good, broken and lazy alike (the file does not exist, so
`exists: false` is true). It is a *tautological* check: it scores every agent
100% and therefore contributes zero discriminating power.

## Decisive check to neuter
The check that separates the lazy agent from the good agent is the decisive one.
In the shipped fixture the lazy agent writes `output.json` but no `summary.md`,
so neutering `summary_file` drops power vs lazy to 0. If the lazy agent were
satisfied by a subset of checks, neutering the *last* check it satisfies is the
decisive mutation.

## Command
```
python3 scripts/verify_harness.py \
  --checks checks.json --contract contract.json \
  --good good --broken broken --lazy lazy \
  --neutered-checks checks_neutered.json --json report.json
```
Exit 0 means the live run passed *and* the neutered run dropped power. Exit 1 means
either the live run failed or the harness could not detect the dead check.

## Near-miss triggers
- Neutering a check and the power does not change -> the check had no power to begin
  with, or the harness does not aggregate it. Halt.
- Neutering a check and the harness still exits 0 -> the verifier is not verified.
- Neutering *all* checks to prove the harness works -> the test is meaningless; use
  exactly one.
- A neutered check that is not actually always-pass (it fails for the good agent)
  -> the mutation is not a mutation. Verify the neutered check passes for good.
