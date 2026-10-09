# EVALS — module-contract-first (retrieved 2026-10-07, host Biest)

Each prompt below includes expected behaviour and failure signs.

## Prompt 1 — New module with public API
**Prompt:** "I added a new module  with exports , , and  class. Set up contract tracking."
**Expected behaviour:** Agent runs , commits snapshot, writes boundary doc listing allowed importers, adds drift test to CI config.
**Failure signs:** Snapshot missing or empty; no boundary doc; drift test not wired into CI.

## Prompt 2 — Breaking change without version bump
**Prompt:** "I changed  to  in payments module. Merge this PR."
**Expected behaviour:** Agent detects breaking signature change via , blocks merge, asks for major version bump or reversion.
**Failure signs:** Agent says "looks fine" and merges; no version bump requested; drift test not run.

## Prompt 3 — Hand-edited snapshot hiding drift
**Prompt:** "I added export  but the snapshot still shows old symbols. Can you check?"
**Expected behaviour:** Agent runs , sees DRIFT DETECTED for new_func, asks developer to regenerate snapshot via  and commit both together.
**Failure signs:** Agent ignores drift; snapshot manually edited without regeneration; merge proceeds with mismatch.

## Prompt 4 — Import cycle between modules
**Prompt:** "Module A imports B and B imports A. Fix it."
**Expected behaviour:** Agent runs , detects CYCLE DETECTED A -> B -> A, suggests extracting shared types into internal-only utility module.
**Failure signs:** Cycle not detected; agent suggests circular import as acceptable; no boundary doc update.

## Prompt 5 — Empty module edge case
**Prompt:** "Module X has no exports yet. What does the contract look like?"
**Expected behaviour:** Snapshot shows empty symbols list;  passes when live is also empty; agent notes that adding first export triggers drift detection automatically.
**Failure signs:** Snapshot missing treated as error instead of full-add drift; agent says no contract needed for empty module.
