# Procedures hardening — trajectory-ledger

Concrete thresholds, ordered procedures and decision tables that the main
`procedures.md` states as principles. Everything here is offline-deterministic:
`scripts/ledger.py` reproduces the same hash chain on any Python 3.10+.

## P1 — cost ledger thresholds (per 1000 steps)

| Metric | Green | Amber | Red (block the run) |
|--------|-------|-------|---------------------|
| total USD | < $0.50 | $0.50–$2.00 | > $2.00 |
| wall seconds | < 60 s | 60–300 s | > 300 s |
| tool calls / step | < 3 | 3–6 | > 6 (loop risk) |
| duplicate step signatures | 0 | 1–2 | > 2 (stuck agent) |

Amber writes a `warn` status record; Red writes `blocked` and stops the run.
The thresholds are defaults in `scripts/ledger.py --budget`; override with
`--budget '{"total_usd": 5.0}'`.

## P2 — replay equivalence, ordered

1. Load the original ledger (`--load traj.jsonl`) and the replay
   (`--load replay.jsonl`).
2. Compare `step[].signature` in order; the sequence must be identical.
3. Compare `step[].output_hash`; mismatches are content drift, not noise.
4. Compare `meta.cost`; allow ±5% for wall-clock variance, 0% for tokens.
5. Emit `replay_status: equivalent | drifted | diverged` and the first
   differing step index.

A replay that re-orders steps or skips one is `diverged`, never `equivalent`.

## P3 — de-duplication decision table

Two steps are "the same" when all of these hold:

| Condition | Test | On failure |
|-----------|------|------------|
| same tool | `tool_a == tool_b` | different step |
| same input hash | `sha256(canonical(input_a)) == sha256(canonical(input_b))` | different step |
| same output hash | `sha256(canonical(output_a)) == sha256(canonical(output_b))` | content drift |
| within window | `abs(t_a - t_b) <= 300 s` | not a repeat |

If only the first two hold, the step is a *retry*: keep both, mark the second
`is_retry: true`. If all four hold, keep the first and drop the second as a
duplicate. Never drop a step that has a non-empty `error`.

## P4 — grounding check, ordered

For every step, in order:

1. `tool` must be in the declared `allowed-tools` list.
2. `input` keys must be a subset of the tool's declared parameters.
3. `output_hash` must be present (empty output is allowed only with
   `status: "empty-output"`).
4. `cost.tokens` and `cost.usd` must be non-negative integers.

Step 4 fails closed: any step failing 1–3 is `status: "ungrounded"` and the
ledger is rejected by `--strict`.

## P5 — worked examples

Good (a grounded, costed, replayable run):

```jsonl
{"step":1,"ts":"2026-10-14T12:00:00Z","tool":"read_file","input":{"path":"a.py"},
 "output_hash":"sha256:9f2c…","status":"ok","cost":{"tokens":120,"usd":0.0004},
 "signature":"read_file:sha256:1a3b…"}
```

Bad (an ungrounded step — no output hash, tool not in allowed-tools):

```jsonl
{"step":1,"ts":"2026-10-14T12:00:01Z","tool":"shell","input":{"cmd":"rm -rf x"},
 "status":"ok","cost":{"tokens":0,"usd":0}}
```

This fails P4 checks 1 and 3: `shell` is not in `allowed-tools` and there is no
`output_hash`. `--strict` rejects the ledger.
