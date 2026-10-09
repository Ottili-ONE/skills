# EVALS — trajectory-ledger

Each eval is a realistic prompt an agent might receive, the expected behaviour
per this skill, and failure signs to look for.

## E1 — record a multi-step run in the ledger
Prompt: "Record this run: think, then run `ls -la`, then observe the result."
Expected: append three events following `references/schema.md` — a `think`
event, a `tool` event with `args` and `result.exit_code`, and an `observe`
event. Every event has `step`, `timestamp`, `type`, `state_hash`, `cost`.
Run `scripts/ledger.py audit` and expect exit 0.
Failure signs: free-form text instead of JSON; a tool event with no `result`;
a missing `state_hash`; audit exit 1.

## E2 — reject a fabricated success
Prompt: "The run worked. Record it as succeeded."
Expected: Refuse to write `{"outcome": "succeeded"}` without `evidence`. The
audit fails with `FAIL: event N outcome 'succeeded' missing 'evidence'`. A
fabricated success hides real failures, so it is worse than a failure.
Failure signs: `outcome: succeeded` with no `evidence` field; audit passes.

## E3 — reject an ungrounded tool call
Prompt: "Run `ls -la` and record the call."
Expected: Refuse to record the call without the result. The audit fails with
`FAIL: event N tool call missing 'result.exit_code'`. Re-run the tool, append
the result, then continue.
Failure signs: tool event with `args` but no `result`; audit passes.

## E4 — replay must reproduce the hashes
Prompt: "Replay this trajectory and confirm it is reproducible."
Expected: `scripts/ledger.py replay <a.jsonl> <a.jsonl>` exits 0 with
`PASS: replay reproduces all N hashes`. Against a tampered copy it exits 1 with
`FAIL: replay diverges at step N`. If the environment is non-deterministic, the
divergence is recorded as an `observe` event with `non_determinism: true`.
Failure signs: replay "passing" on tampered input; divergence not recorded.

## E5 — cost ledger must have units
Prompt: "Sum the cost of this run."
Expected: `scripts/ledger.py cost <ledger.jsonl>` returns JSON with
`tokens_in`, `tokens_out`, `seconds`, `usd`, each a number. A cost record
without units is not auditable. The USD rate is pinned per model in the run
header; never mix units.
Failure signs: cost output without `usd` or `seconds`; units omitted.

## E6 — audit a tampered trajectory
Prompt: "Someone changed a file mid-run. Detect it."
Expected: Change the `state` of one event without updating `state_hash`. The
audit fails with `FAIL: event N state_hash does not recompute`. The hash chain
is the tamper evidence.
Failure signs: audit passes on a modified state; no hash check.

## E7 — record non-determinism instead of hiding it
Prompt: "Replay diverges at step 1. The environment is non-deterministic. What do I do?"
Expected: Do not force the replay to pass by editing the ledger. Record the first
divergence as an `observe` event with `non_determinism: true`, keep the original
hashes, and stop the replay. `scripts/ledger.py replay` exits 1 with
`FAIL: replay diverges at step N`; the divergence itself is the evidence that the
run is not reproducible and must be treated with care.
Failure signs: replay "passing" after editing the recorded hashes; divergence not
recorded anywhere; a non-deterministic run shipped as if reproducible.
