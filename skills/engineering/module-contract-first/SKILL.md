---
name: module-contract-first
description: "Designs and enforces module contracts in one working tree: public API surface, versioned schemas, drift tests against reference snapshots, and boundary rules between sibling modules so a change in one module cannot silently break another."
license: MIT-compat
compatibility: "framework-agnostic; Python/TypeScript/Postgres; Ottili modules"
metadata: {}
allowed-tools: []
---
# Module Contract First Skill — Quick Reference (body <500 lines; full procedure in references/module-contract-procedure.md)

## When to use this skill (trigger)
- You are starting a new module or adding public exports to an existing one.
- A consumer imports a symbol that is not in the committed contract snapshot.
- You need to decide whether a change is breaking (major bump) or non-breaking (minor/patch).
- Sibling modules import each other and you must enforce a boundary (no cycles).
- CI is red with "DRIFT DETECTED" or "CYCLE DETECTED".

## When NOT to use this skill
- Private/internal helpers that no consumer imports (they are not part of the public surface).
- Single-file scripts with no consumers and no planned exports.
- Fully greenfield work where no other module depends on the output yet.

## Decision table — change classification
| Change | Semver | Action |
|--------|--------|--------|
| Add new export, route, table, or message | minor | regenerate snapshot, commit both together |
| Rename export, change signature, remove export | major | bump major, notify all consumers, regenerate snapshot |
| Add optional field to a request object | patch | regenerate snapshot only |
| Change field type or required->optional | major | bump major, regenerate snapshot, update consumers |

## Numbered procedure (summary; full recipe in references/module-contract-procedure.md)
1. **Enumerate the public surface** — run `python3 scripts/check_contract_drift.py --enumerate <module-dir>` and commit the generated snapshot as the source of truth.
2. **Freeze and version** — tag the snapshot commit with semver per the decision table; never hand-edit a committed snapshot.
3. **Write the drift test** — `python3 scripts/check_contract_drift.py --check <module-dir>` must run in CI on every PR; exit 1 on any drift.
4. **Enforce boundaries** — run `python3 scripts/check_contract_drift.py --cycles <root>`; any back-edge is an automatic fail.
5. **Document the boundary** — write a boundary doc listing allowed importers and forbidden import directions.

## Pitfalls from research (real incidents)
- Hand-edited snapshots hide new exports; the next `--check` shows full-add drift and CI goes red until regenerated honestly alongside the code change in the same PR.
- A snapshot that is not regenerated on every PR touching public API surface is the #1 cause of silent breakage across Ottili modules.
- Import cycles break static analysis tooling downstream even when snapshots match; cycle detection is an automatic fail regardless of snapshot state.
- An empty module must have an empty snapshot; a missing snapshot file is treated as full-add drift, not an error.

## Near-miss trigger prompts (act on these immediately)
- "I added an export but forgot to update the snapshot" — run `--check` before committing; if drift, regenerate then commit both files together.
- "Module A imports B and B imports A" — run `--cycles` immediately; extract shared types into an internal-only module.
- "The snapshot looks right but CI is red" — diff spans >5 lines with no corresponding code change = probable manual edit; block merge.

## Verification checklist (all must pass before you finish)
- [ ] Snapshot regenerated via `--enumerate`, never hand-edited
- [ ] `--check` exits 0 against the committed snapshot
- [ ] `--cycles` reports no back-edges
- [ ] Semver bump matches the change classification in the decision table
- [ ] Boundary doc lists allowed importers and forbidden directions
- [ ] Drift test is wired into CI config
- [ ] Enumeration completes in <2s for modules under 500 symbols
