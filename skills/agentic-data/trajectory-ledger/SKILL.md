---
name: trajectory-ledger
description: "Schema, grounding rules, outcome status and cost ledgers for agent trajectories. Use when an agent must record, replay or audit a multi-step run (task, tools, state transitions, cost, outcome) so that results are reproducible and auditable; not for logging application telemetry."
compatibility: Python 3.10+, JSONL storage; verified 2026-10-09
license: MIT
---
# Trajectory Ledger

Trigger: recording, replaying or auditing a multi-step agent run so that the
result is reproducible and auditable.

## Procedure (numbered — follow in order)
1. **Define the schema first** — every trajectory is a JSONL file of events:
   `step`, `timestamp`, `type` (tool/think/observe), `tool`, `args`, `result`,
   `state_hash`, `cost`. Never free-form text in the ledger.
2. **Hash the state at every step** — `state_hash = sha256(canonical(state))`.
   A missing or mismatched hash means the trajectory was tampered with or the
   replay diverged.
3. **Ground every tool call** — record the exact command and its exit code; a
   tool call with no recorded result is ungrounded and must be re-run.
4. **Track outcome status** — `pending` -> `running` -> `succeeded` | `failed` |
   `blocked` | `timeout`. Never mark `succeeded` without evidence.
5. **Record cost** — tokens in/out, wall-clock, tool calls, retries. A cost
   ledger without a unit is not a ledger.
6. **Enable replay** — given a trajectory and the same inputs, re-running must
   reproduce the same `state_hash` sequence. If it diverges, the run was not
   deterministic.
7. **Audit** — walk the ledger: every `succeeded` has a result, every `failed`
   has a reason, every hash matches, and the cost ledger sums.

## Decision tables
- **Outcome status**: `succeeded` requires a recorded result; `failed` requires a
  reason; `blocked` requires the blocker; `timeout` requires the elapsed time.
- **Grounding**: tool call + result = grounded; tool call without result =
  ungrounded, re-run; no tool call = not grounded, mark `blocked`.
- **Replay**: hashes match = reproducible; first divergence = non-determinism,
  record it and stop the replay.
- **Cost units**: tokens = model counts; time = seconds; money = USD at the
  pinned rate. Never mix units.

## Near-miss triggers (stop and re-check before proceeding)
- A `succeeded` event with no result -> fabricated success.
- A tool call whose `args` were not recorded -> the run is not reproducible.
- `state_hash` missing on any step -> the trajectory can be tampered with.
- Replay diverges at step 1 -> the environment is non-deterministic; record it.
- Cost recorded without units -> not auditable.

## Pitfalls from research
- P1: Free-form logs are not a ledger; they cannot be replayed or audited.
- P2: Missing state hashes let tampering go undetected.
- P3: `succeeded` without a recorded result is a fabricated success.
- P4: Unrecorded tool args make replay impossible.
- P5: Non-deterministic environments must be recorded, not hidden.

## Verification checklist
- [ ] Schema defined and documented.
- [ ] Every step has a `state_hash`.
- [ ] Every tool call has recorded args and result.
- [ ] Outcome status has evidence for every terminal event.
- [ ] Cost has units.
- [ ] Replay reproduces the hash sequence (or divergence is recorded).
- [ ] Audit walk passes.

## References
- procedures: references/procedures.md
- schema: references/schema.md
- EVALS: references/EVALS.md
- SOURCES: references/SOURCES.md
- scripts: scripts/ledger.py
