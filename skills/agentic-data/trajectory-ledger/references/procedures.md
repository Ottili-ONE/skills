# Procedures — trajectory-ledger

Verified 2026-10-09. Version-sensitive: schema fields change; bump the schema
version and re-run the audit when a field is added or removed.

## 0. The core invariant
A trajectory is auditable only if every step is (a) typed, (b) hashed, and
(c) grounded. A free-form log is not a trajectory.

## 1. Schema first
Adopt `references/schema.md`. Every event is a JSON object with `step`,
`timestamp`, `type`, `state_hash`, `cost`. Write the schema version into the
first event (`"schema": "trajectory-ledger-v1"`).

## 2. Hashing
`state_hash = sha256(canonical_json(state))` where `canonical_json` sorts keys
and uses `ensure_ascii=False`. Compute the hash *after* the state changes, and
store the state itself in the same event so the hash can be recomputed.

## 3. Grounding
Every `tool` event must have `args` and `result` with an `exit_code`. A tool
call without a recorded result is ungrounded: re-run it and append the result
before continuing.

## 4. Outcome status
| Status | Required field |
|--------|----------------|
| `succeeded` | `evidence` |
| `failed` | `reason` |
| `blocked` | `blocker` |
| `timeout` | `elapsed_seconds` |

Never mark `succeeded` without evidence. A fabricated success is worse than a
failure because it hides the failure.

## 5. Cost ledger
Every event carries `cost` with `tokens_in`, `tokens_out`, `seconds`, `usd`.
The USD rate is pinned per model and recorded in the run header; never mix
units or omit them.

## 6. Replay
Replay is the test: given the trajectory and the same inputs, re-running must
reproduce the same `state_hash` sequence. Walk the hashes; the first divergence
is non-determinism — record it in the ledger as an `observe` event with
`non_determinism: true` and stop the replay.

## 7. Audit walk
For every event: `type` is valid, `state_hash` recomputes to the stored value,
every `tool` has args and result, every terminal event has its required field,
and cost sums across the run. `scripts/ledger.py audit` performs this walk.

## Worked examples

Good — grounded tool event:
```json
{"type": "tool", "tool": "shell", "args": {"cmd": "ls -la"},
 "result": {"exit_code": 0, "stdout": "total 0\n", "stderr": ""},
 "state_hash": "sha256:abc", "cost": {"tokens_in": 0, "tokens_out": 0, "seconds": 0.1, "usd": 0.0}}
```

Bad — ungrounded tool event:
```json
{"type": "tool", "tool": "shell", "args": {"cmd": "ls -la"}}
```

Good — terminal with evidence:
```json
{"outcome": "succeeded", "evidence": "output.json: status ok"}
```

Bad — fabricated success:
```json
{"outcome": "succeeded"}
```
