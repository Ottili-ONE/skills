# Cost ledger — trajectory-ledger

A trajectory that cannot be costed cannot be budgeted. Every event carries a
`cost` object; `scripts/ledger.py cost` sums them. This page records the unit
contract and the audit rules.

## Units (never mix)

| Field | Unit | Source |
|-------|------|--------|
| `cost.tokens_in` | model input tokens | tokenizer count |
| `cost.tokens_out` | model output tokens | tokenizer count |
| `cost.seconds` | wall-clock seconds | monotonic clock |
| `cost.usd` | USD | `tokens * rate` at the pinned rate |

## Rate pinning

The USD rate is pinned **per model** in the run header, never computed on the
fly. A run that changes model mid-way carries two rate entries; the cost ledger
tags each event with the rate id it used. Example run header:

```json
{"run_id": "...", "rates": {"gpt-4o-2024-08-06": 0.0000025, "claude-3-5-sonnet-20241022": 0.000003}}
```

## Ordered audit

1. **Sum tokens** — `tokens_in` and `tokens_out` across all events. Cross-check
   against the model provider's reported usage if available.
2. **Sum time** — `seconds` across all events. This is wall-clock, so it will
   never equal the sum of model latency alone; transport and tool time are
   included by design.
3. **Sum money** — `usd` across all events. Recompute from `tokens * rate` and
   compare; a mismatch means a rate was applied to the wrong model.
4. **Check units** — every event's `cost` has all four fields. An event missing
   a field is flagged, not zero-filled.
5. **Report** — emit `{"tokens_in", "tokens_out", "seconds", "usd", "rate_ids": [...]}`.

## Decision table

| Situation | Action |
|-----------|--------|
| Event missing `cost` entirely | FAIL: uncostable event |
| `cost.usd` present but `tokens` zero | WARN: manually priced event; tag it |
| Rate id not in the run header | FAIL: unknown rate |
| `seconds` negative | FAIL: monotonic clock went backwards |
| Tokens exceed the model's context window | FAIL: impossible count, suspect tampering |

## Near-miss triggers

- Summing `usd` from two runs with different models and calling it "total cost"
  -> the rates differ. Tag by rate id.
- Recording `cost` as a single number -> the unit is lost. Always use the object.
- Using provider-reported tokens for one model and local tokenizer counts for
  another -> the counts are not comparable. Pick one counting method per run.
- A `timeout` outcome with `cost.seconds` equal to the timeout -> the event was
  cut off; the cost is a lower bound, not the true cost. Mark it.
