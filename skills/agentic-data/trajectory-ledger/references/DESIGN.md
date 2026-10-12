# DESIGN: trajectory-ledger

## Trigger description (SKILL.md description draft, <=1024 chars)
"Schema, grounding rules, outcome status and cost ledgers for agent trajectories. Use
when an agent must record, replay or audit a multi-step run (task, tools, state
transitions, cost, outcome) so that results are reproducible and auditable; not for
logging application telemetry."

## Procedure outline
1. Record every step as a typed event (tool, observe, state, outcome) in JSONL with a
   schema version (`trajectory-ledger-v1`).
2. Every tool call records its args AND its result. A call without a result is
   ungrounded — re-run before marking anything succeeded.
3. Every step carries a `state_hash` over the environment state, chained so that any
   tampering breaks the chain.
4. Outcome status requires evidence: `succeeded` needs a recorded result, `failed` needs
   a reason, `blocked` needs the blocker, `timeout` needs the elapsed time. A `succeeded`
   with no result is a fabricated success.
5. Replay by re-running the recorded tool calls and comparing hashes. A match means
   reproducible; the first divergence is non-determinism — record it as an `observe`
   event with `non_determinism: true` and stop the replay.
6. Cost ledger uses single units (tokens, seconds, USD at a pinned rate). Never mix
   units; a field mixing tokens and USD cannot be summed meaningfully.
7. Audit: walk the ledger and assert every succeeded has a result, every failed has a
   reason, every hash matches, and the cost ledger sums.

## Scripts planned
- `scripts/ledger.py` — append events, verify the hash chain, replay against a live
  environment, and audit a ledger file (`ledger.py audit <ledger.jsonl>`).

## Five eval scenarios (expanded in `references/EVALS.md`)
1. "A `succeeded` event has no result field. Is the run valid?" -> No: fabricated success.
2. "A tool call's args were not recorded. Can I replay it?" -> No: unrecorded args make
   replay impossible.
3. "Replay diverges at step 1. What do I do?" -> The environment is non-deterministic;
   record the divergence as an `observe` event and stop the replay.
4. "My cost field mixes tokens and USD. Is that a problem?" -> Yes: it cannot be summed
   meaningfully; use one unit per field.
5. "A `tool` event has a `type` but no `tool` field." -> Malformed event; reject it.

## What this skill does better than a generic agent
A generic agent writes free-form logs that cannot be replayed or audited. This skill
ships a typed schema, a chained state hash, grounding rules that distinguish real from
fabricated success, a non-determinism handling procedure, and an audit command. It
prevents the common incident of a "reproducible" run whose logs were written after the
fact and cannot be replayed.

## What existing public skills do (and what this one does differently)

Surveyed on 2026-10-12. No public Agent Skill covers agent trajectory ledgers. The
closest artefacts are logging libraries and ML training logs, which record events
but cannot be replayed or audited for grounding. `anthropics/skills`, the Fastio
2026 directory and `skills.cat` have no entry for this topic.

This skill is the only one that makes a trajectory *reproducible* rather than merely
recorded:
- **Typed schema (`trajectory-ledger-v1`)**: every event is one of `tool`,
  `observe`, `state`, `outcome`. Free-form logs cannot be audited because "did it
  really run?" has no answer.
- **Grounding rules**: a `succeeded` outcome with no recorded result is a fabricated
  success; a `failed` outcome needs a reason; a `blocked` outcome needs the blocker;
  a `timeout` needs elapsed time. Every tool call records args AND result.
- **Chained `state_hash`**: each step's hash covers the previous hash, so any
  post-hoc editing of the ledger breaks the chain and is detected on audit.
- **Replay with divergence handling**: re-run recorded tool calls and compare
  hashes. The first divergence is non-determinism — recorded as an `observe` event
  with `non_determinism: true`, then replay stops. It does not silently pass.
- **Cost ledger in single units**: tokens, seconds, USD at a pinned rate. A field
  mixing tokens and USD cannot be summed meaningfully.

Public sources surveyed (2026-10-12, all HTTP 200):
| Source | What it has | Gap this skill fills |
|--------|-------------|---------------------|
| JSON Schema / JSONL tooling | schema syntax | no grounding rules, no replay, no cost ledger |
| ML training logs | event recording | not replayable, no audit command |
| `anthropics/skills` / Fastio 2026 / `skills.cat` | no trajectory entry | the whole category is missing |
