---
title: Engineering Playbooks — Ottili ONE Skills
---

# Engineering Playbooks

Ten opinionated, testable skills for Ottili engineering lanes. Each one is a **contract**: a
trigger, a decision table, a checker script, and an `EVALS.md` with real prompts. Install with
`scripts/install.sh --target <agent-dir> <skill-name>` or copy the folder.

## Skills

| Skill | One-line value | Install hint |
|-------|----------------|--------------|
| [acceptance-harness](./acceptance-harness/SKILL.md) | Turns "did it work?" into a PASS/FAIL/BLOCKED verdict with evidence. | `install.sh --target agents acceptance-harness` |
| [foundation-v2-conformance](./foundation-v2-conformance/SKILL.md) | Stops agents from inventing styling/workarounds that break on the next Foundation v2 release. | `install.sh --target agents foundation-v2-conformance` |
| [honest-status](./honest-status/SKILL.md) | Replaces `DONE`/`VERIFIED` prose with auditable status + evidence + ticket. | `install.sh --target agents honest-status` |
| [long-test-discipline](./long-test-discipline/SKILL.md) | Runs minute-scale tests in the foreground with a wrapper, a recorded seed and a JSON record. | `install.sh --target agents long-test-discipline` |
| [module-contract-first](./module-contract-first/SKILL.md) | Forces a versioned public API + snapshot before any implementation starts. | `install.sh --target agents module-contract-first` |
| [outbox-idempotency](./outbox-idempotency/SKILL.md) | Makes duplicate publishes and crash-replays safe via one-transaction outbox + idempotency key. | `install.sh --target agents outbox-idempotency` |
| [pg-rls-multitenant](./pg-rls-multitenant/SKILL.md) | Tenant-key-first Postgres RLS with FORCE, expand/contract migrations and automated leak tests. | `install.sh --target agents pg-rls-multitenant` |
| [playwright-a11y-e2e](./playwright-a11y-e2e/SKILL.md) | `getByTestId` selectors, unweakened axe rules, keyboard traversal incl. shadow DOM. | `install.sh --target agents playwright-a11y-e2e` |
| [problem-json-contracts](./problem-json-contracts/SKILL.md) | RFC 9457 problem details with a catalogue, OpenAPI sync and duplicate-code detection. | `install.sh --target agents problem-json-contracts` |
| [shared-tree-git](./shared-tree-git/SKILL.md) | Commits only your own paths on a shared tree; checks `index.lock` PID liveness first. | `install.sh --target agents shared-tree-git` |

## Evals

Every skill ships `references/EVALS.md` with **5+ realistic prompts** (expected behaviour +
failure signs + "what the skill changes vs no skill") and **3+ near-miss prompts** (act before
the incident). Run the prompts mentally against the SKILL.md, and where a script exists, with a
real input:

```
python3 scripts/validate_skill.py --all
python3 scripts/validate.py
```

## Cross-links

The `## Related skills` section of every SKILL.md links to sibling skills by name. The graph is
**acyclic**: `shared-tree-git` is the unique sink (it has no outgoing edges) and every other skill
reaches it transitively. Verify with:

```
python3 scripts/check_shared_tree.py scan -- skills/engineering
```
