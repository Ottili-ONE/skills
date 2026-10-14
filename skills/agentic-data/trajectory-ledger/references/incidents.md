# Incidents — trajectory-ledger

Real ledger failures, the observable signature that exposes them, and the
exact recovery procedure. Each incident is a case a generic agent gets wrong
because it wrote a free-form log and called it a ledger.

## I1 — Fabricated success

- **What happened**: a run was recorded as `{"outcome": "succeeded"}` with no
  `evidence` and no recorded result. The audit passed because nothing checked
  for it. The run had actually failed at step 2.
- **Observable signature**: a terminal event with `outcome: succeeded` and no
  `evidence` field; or a `tool` event with `args` but no `result.exit_code`.
- **Recovery**: re-run the tool, append the real result, add `evidence` to the
  terminal event. A `succeeded` with no result is a fabricated success and is
  worse than a failure because it hides real failures.
- **Prevention**: `scripts/ledger.py audit` requires `evidence` on every
  `succeeded`, `reason` on every `failed`, `blocker` on every `blocked` and
  `elapsed_seconds` on every `timeout`.

## I2 — Ledger written after the fact

- **What happened**: an agent wrote a free-form paragraph describing a run and
  called it a trajectory. There was no tool, no args, no result, no hash and no
  outcome field. It could not be replayed or audited.
- **Observable signature**: lines that are not JSON objects; events missing
  `step`, `timestamp`, `type`, `state_hash` or `cost`.
- **Recovery**: re-record the run as typed events following
  `references/schema.md`, or normalise what exists with
  `scripts/ledger.py normalize <in.jsonl> <out.jsonl>` and re-audit.
- **Prevention**: the schema is typed and every mandatory field is checked.

## I3 — Hash chain silently broken

- **What happened**: an event's `state` was edited mid-run to hide a mistake,
  but the `state_hash` was not updated. The audit passed because nobody
  recomputed the hash. The tampering was invisible.
- **Observable signature**: `state_hash` present but not equal to
  `sha256(canonical(state))`.
- **Recovery**: recompute every hash; if the stored hash does not match, the
  event was tampered with or mis-recorded. Reject the ledger and re-record.
- **Prevention**: `scripts/ledger.py audit` recomputes `state_hash` from
  `state` on every event that carries one.

## I4 — Non-determinism treated as failure

- **What happened**: replay diverged at step 1 because the environment returns
  timestamps. The agent edited the recorded hashes to make replay pass and
  shipped the run as reproducible. It was not.
- **Observable signature**: replay exits 0 after the recorded hashes were
  edited; no `non_determinism` record anywhere in the ledger.
- **Recovery**: record the first divergence as an `observe` event with
  `non_determinism: true` using
  `scripts/ledger.py record-non-det <ledger.jsonl> <step> "<reason>"`, keep the
  original hashes, and stop the replay. A divergent run is not reproducible and
  must be treated with care.
- **Prevention**: `record-non-det` appends the record with a step strictly
  greater than the last recorded step; editing an existing hash to force a
  pass is forgery and the audit would then pass on a run that was never
  reproducible.

## I5 — Steps written out of order

- **What happened**: an agent grouped events by type when writing the file, so
  the steps ran 0, 2, 1. Every individual event was valid and the hash chain
  looked intact, but the ledger was not a sequence and replay was meaningless.
- **Observable signature**: `step` values not strictly increasing; audit fails
  with `FAIL: event N step X is not strictly greater than event Y step Z`.
- **Recovery**: re-order the events by step and re-audit. Reordering changes
  the hash chain even when every event is individually valid.
- **Prevention**: the audit enforces strict step monotonicity.

## I6 — Wrong schema version

- **What happened**: a ledger was written against a draft schema that omitted
  the `cost` field. It audited clean against the draft rules but could not be
  replayed against the current schema, and the replay tool silently produced
  wrong results.
- **Observable signature**: no event declares `schema`, or the declared schema
  is not `trajectory-ledger-v1`, or the file mixes versions.
- **Recovery**: re-write against the current schema in `references/schema.md`.
- **Prevention**: the audit requires the first event to declare
  `schema: trajectory-ledger-v1` and rejects mixed versions.
