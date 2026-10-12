# Normalisation and non-determinism — trajectory-ledger

Two ledger operations that close the gap between "I wrote the log" and "the log
is auditable": normalising a hand-written trajectory, and recording a replay
divergence without forging the hashes.

## Normalise
`scripts/ledger.py normalize <in.jsonl> <out.jsonl>`

Hand-written trajectories are often not canonical: keys in arbitrary order,
`state_hash` missing or stale, non-`sort_keys` serialisation. Normalisation
rewrites every line with `json.dumps(..., sort_keys=True, ensure_ascii=False,
separators=(",", ":"))` and recomputes `state_hash` from any event that carries
a `state`. Events without a `state` keep their existing hash.

Why this matters: the audit recomputes `state_hash` from `state`. A hand-written
event whose hash does not recompute fails the audit even though the agent
"recorded" it correctly. Normalise first, audit second.

## Record non-determinism
`scripts/ledger.py record-non-det <ledger.jsonl> <step> "<reason>"`

The replay procedure says: on first divergence, record it and stop. This
subcommand appends an `observe` event:

```json
{"step": 1, "type": "observe", "non_determinism": true,
 "reason": "timestamps drifted between runs",
 "state": {"divergence_at_step": 1, "reason": "timestamps drifted between runs"},
 "state_hash": "sha256:...",
 "cost": {"tokens_in": 0, "tokens_out": 0, "seconds": 0.0, "usd": 0.0}}
```

The hash is recomputed from the recorded state, so the event itself is
grounded. The divergence is now *in* the ledger, auditable, and the ledger is
honest about the run not being reproducible.

## What must never happen
- Editing an existing `state_hash` to make replay pass. This forges the ledger:
  the audit would then pass on a run that was never reproducible.
- Deleting the divergent event. The divergence is the evidence.
- Marking the run `succeeded` after a divergence. A non-reproducible run is not
  a succeeded run; it is a run that must be treated with care.

## Near-miss triggers
- A normalised file that still fails audit -> an event without `state` whose
  stored hash is wrong. Either the state was lost or the hash was forged.
- `record-non-det` on a step that already has an event -> the step number is
  the *next* step, not the divergent one. The divergence is recorded at the
  step that follows the last matching hash.
- A ledger where every replay passes but the environment is known to be
  non-deterministic -> the hashes were edited. Audit the provenance.
