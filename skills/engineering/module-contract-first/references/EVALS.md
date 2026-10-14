# EVALS — module-contract-first
Retrieval date: 2026-10-14 (pass 3 re-verification). Verified versions: OpenAPI v3.1.0, JSON Schema Draft
2020-12, SemVer 2.0.0, `scripts/check_contract_drift.py` v1. Sources:
references/SOURCES.md.

Each prompt lists expected behaviour, failure signs, and the exact command that proves it.

## E1 — New module with a public API
**Prompt**: "I added a new module `payments` with exports `create_invoice`,
`Invoice` class, and `refund` function. Set up contract tracking."
**Expected**: Agent runs `check_contract_drift.py --enumerate payments`, commits the
snapshot to `payments/module-contracts/payments.json`, writes a boundary doc listing
allowed importers, and adds the drift test to CI.
**Exact command to verify**:
`python3 scripts/check_contract_drift.py --enumerate payments` then
`python3 scripts/check_contract_drift.py --check payments` exits 0.
**Failure signs**: snapshot missing or empty; no boundary doc; drift test not wired into CI.
**What the skill changes vs no skill**: without the skill an agent adds `payments` with `create_invoice`, `Invoice` and `refund` and ships it with no record of the surface. The skill makes `--enumerate` produce the snapshot, the boundary doc list allowed importers, and the drift test wire into CI, so the public surface is versioned before it is used by anyone.
**Worked example good**: snapshot `{"symbols": ["Invoice", "create_invoice", "refund"]}`
sorted, deduplicated, produced by `--enumerate`.
**Worked example bad**: snapshot hand-edited with `["create_invoice", "create_invoice"]`
(duplicate).

## E2 — Breaking change without a version bump
**Prompt**: "I changed `create_invoice(amount: int)` to `create_invoice(amount: Decimal)`
in the payments module. Merge this PR."
**Expected**: Agent detects the breaking signature change via `--check`, blocks merge,
asks for a major version bump or a reversion.
**Failure signs**: agent says "looks fine" and merges; no version bump requested; drift detected by `--check` and merge proceeds anyway.
**What the skill changes vs no skill**: without the skill an agent changes `create_invoice(amount: int)` to `create_invoice(amount: Decimal)`, says "looks fine" and merges. The skill makes `--check` exit 1 with `DRIFT DETECTED` and blocks merge until there is a major bump or a reversion, so a breaking signature change is never a silent patch.
**Exact command to verify**: `check_contract_drift.py --check payments` exits 1 with
`DRIFT DETECTED` when the live surface diverges from the snapshot.

## E3 — Hand-edited snapshot hiding drift
**Prompt**: "I added export `new_func` but the snapshot still shows the old symbols.
Can you check?"
**Expected**: Agent runs `--check`, sees `DRIFT DETECTED` for `new_func`, asks the
developer to regenerate the snapshot via `--enumerate` and commit both files together in
the same PR (never separate commits).
**Failure signs**: agent ignores drift; snapshot manually edited without regeneration; merge proceeds with mismatch.
**What the skill changes vs no skill**: without the skill an agent hand-edits the snapshot to hide `new_func` and the drift test passes on a lie. The skill makes regeneration via `--enumerate` the only valid path and requires both files to be committed in the same PR, so a hand-edited snapshot is a blocked merge, not a green CI.
## E4 — Import cycle between modules
**Prompt**: "Module A imports B and B imports A. Fix it."
**Expected**: Agent runs `check_contract_drift.py --cycles root`, detects
`CYCLE DETECTED A -> B -> A`, suggests extracting shared types into an internal-only
utility module that neither side exports publicly, and updates the boundary doc with
the forbidden import list.
**Failure signs**: cycle not detected; agent suggests circular import as acceptable; no **What the skill changes vs no skill**: without the skill an agent treats `A -> B -> A` as a small cycle and leaves it. The skill makes `--cycles` the first response and forces shared types into an internal-only module plus a boundary-doc update, so a circular dependency is broken, not accepted.
**Exact command to verify**:
`python3 scripts/check_contract_drift.py --cycles .` exits 0 when no cycle exists.

## E5 — Empty module edge case
**Prompt**: "Module X has no exports yet. What does the contract look like?"
**Expected**: Snapshot shows an empty `symbols` list; `--check` passes when live is also
empty; agent notes that adding the first export triggers drift detection automatically.
**Failure signs**: snapshot missing treated as an error instead of full-add drift, or agent says no contract is needed for an empty module.
**What the skill changes vs no skill**: without the skill an agent says an empty module needs no contract. The skill makes the empty snapshot the correct artefact and treats a missing snapshot file as full-add drift, so "no contract needed" is never a review outcome.
**Worked example good**: `{"symbols": []}` produced by `--enumerate` on an empty module.
**Worked example bad**: no `module-contracts/` directory at all — treat as full-add drift,
not as "no contract needed".

## Near-miss prompts (act before the incident)
- **N1 — "I'll just edit the JSON by hand to add `new_func`."** Answer: no — hand-edited snapshots are suspect by policy; regenerate with `--enumerate` or the drift test is meaningless.
- **N2 — "The snapshot looks right but CI is red."** Answer: diff spans >5 lines with no corresponding code change = probable manual edit; block merge and regenerate.
- **N3 — "Module A imports B and B imports A — that's fine, it's a small cycle."** Answer: no — run `--cycles` immediately; extract shared types into an internal-only module.
- **N4 — "An empty module has no contract."** Answer: no — an empty module gets an empty snapshot; a missing snapshot file is treated as full-add drift, not "no contract needed".
- **N5 — "The breaking change is internal, nobody imports it."** Answer: no — any signature change that breaks a public export blocks merge pending a major version bump or reversion, regardless of current importers.

## Verification checklist
- [ ] Every module has a `module-contracts/<module>.json` snapshot
- [ ] Every snapshot was produced by `--enumerate`, never hand-edited
- [ ] `--check` exits 0 before merge
- [ ] Breaking changes block merge pending a major version bump
- [ ] No import cycles across modules
- [ ] Boundary doc lists allowed importers per module
