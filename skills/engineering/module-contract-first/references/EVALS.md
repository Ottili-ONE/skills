# EVALS — module-contract-first
Retrieval date: 2026-10-13. Verified versions: OpenAPI v3.1.0, JSON Schema Draft
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
**Worked example good**: snapshot `{"symbols": ["Invoice", "create_invoice", "refund"]}`
sorted, deduplicated, produced by `--enumerate`.
**Worked example bad**: snapshot hand-edited with `["create_invoice", "create_invoice"]`
(duplicate).

## E2 — Breaking change without a version bump
**Prompt**: "I changed `create_invoice(amount: int)` to `create_invoice(amount: Decimal)`
in the payments module. Merge this PR."
**Expected**: Agent detects the breaking signature change via `--check`, blocks merge,
asks for a major version bump or a reversion.
**Failure signs**: agent says "looks fine" and merges; no version bump requested; drift
test not run.
**Exact command to verify**: `check_contract_drift.py --check payments` exits 1 with
`DRIFT DETECTED` when the live surface diverges from the snapshot.

## E3 — Hand-edited snapshot hiding drift
**Prompt**: "I added export `new_func` but the snapshot still shows the old symbols.
Can you check?"
**Expected**: Agent runs `--check`, sees `DRIFT DETECTED` for `new_func`, asks the
developer to regenerate the snapshot via `--enumerate` and commit both files together in
the same PR (never separate commits).
**Failure signs**: agent ignores drift; snapshot manually edited without regeneration;
merge proceeds with mismatch.
## E4 — Import cycle between modules
**Prompt**: "Module A imports B and B imports A. Fix it."
**Expected**: Agent runs `check_contract_drift.py --cycles root`, detects
`CYCLE DETECTED A -> B -> A`, suggests extracting shared types into an internal-only
utility module that neither side exports publicly, and updates the boundary doc with
the forbidden import list.
**Failure signs**: cycle not detected; agent suggests circular import as acceptable; no
boundary doc update.
**Exact command to verify**:
`python3 scripts/check_contract_drift.py --cycles .` exits 0 when no cycle exists.

## E5 — Empty module edge case
**Prompt**: "Module X has no exports yet. What does the contract look like?"
**Expected**: Snapshot shows an empty `symbols` list; `--check` passes when live is also
empty; agent notes that adding the first export triggers drift detection automatically.
**Failure signs**: snapshot missing treated as an error instead of full-add drift; agent
says no contract is needed for an empty module.
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
