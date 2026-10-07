# Module Contract First — Full Procedure (retrieved 2026-10-07, host Biest)

## Verified tool versions
- `scripts/check_contract_drift.py` (this repo): v1, offline deterministic, verified on Biest 2026-10-07. Snapshot format: `{"symbols": [...]}` under `module-contracts/<module>.json`.
- OpenAPI v3.1.0: https://spec.openapis.org/oas/v3.1.0 — retrieved 2026-10-07.
- JSON Schema Draft 2020-12: https://json-schema.org/draft/2020-12/json-schema-release-notes.html — retrieved 2026-10-07.
- SemVer 2.0.0: https://semver.org/spec/v2.0.0.html — retrieved 2026-10-07.

## Preconditions
- The module has a `module-contracts/` directory; if missing, create it before enumerating.
- No hand-edited snapshots: any snapshot not produced by `--enumerate` is treated as suspect.

## Step 1 — Enumerate the public surface
```bash
python3 scripts/check_contract_drift.py --enumerate <module-dir>
```
This writes `module-contracts/<module>.json` with the sorted list of top-level exported symbols. Commit the snapshot in the same PR as the code that defines those symbols.

### Worked example — good
```bash
$ python3 scripts/check_contract_drift.py --enumerate src/payments
ok: enumerated 4 symbols -> src/payments/module-contracts/payments.json
$ cat src/payments/module-contracts/payments.json
{
  "symbols": [
    "Charge",
    "Refund",
    "PaymentError",
    "process_payment"
  ]
}
```

### Worked example — bad
A developer hand-edits `payments.json` to add `new_func` but forgets to commit the code change. `--check` then reports full-add drift:
```
DRIFT DETECTED
@@ symbols @@
- old: ['Charge', 'Refund', 'PaymentError', 'process_payment']
+ new: ['Charge', 'Refund', 'PaymentError', 'new_func', 'process_payment']
BLOCKED: merge until snapshot regenerated or reverted
```
Fix: regenerate via `--enumerate` and commit both files together.

## Step 2 — Classify the change and bump semver
| Change | Semver | Action |
|--------|--------|--------|
| Add new export, route, table, or message | minor | regenerate snapshot, commit both together |
| Rename export, change signature, remove export | major | bump major, notify all consumers, regenerate snapshot |
| Add optional field to a request object | patch | regenerate snapshot only |
| Change field type or required->optional | major | bump major, regenerate snapshot, update consumers |

## Step 3 — Write the drift test
`python3 scripts/check_contract_drift.py --check <module-dir>` must run in CI on every PR. Exit 1 on any drift. The snapshot is never hand-edited.

## Step 4 — Enforce boundaries
```bash
python3 scripts/check_contract_drift.py --cycles <root>
```
Any back-edge is an automatic fail. Extract shared types into an internal-only module.

### Worked example — cycle detected
```bash
$ python3 scripts/check_contract_drift.py --cycles src
CYCLE DETECTED
a -> b -> c -> a
Break cycle by extracting shared types into an internal-only module
```

## Step 5 — Document the boundary
Write a boundary doc listing allowed importers and forbidden import directions.

## Schema nullability (conflict recorded)
Sources disagree on whether optional fields should be nullable or omitted entirely. JSON Schema Draft 2020-12 says use `type: ["string", "null"]`; OpenAPI v3.1 moved to `oneOf` with a null type and deprecated `nullable: true`. Resolution: use `oneOf` with a null type in new contracts; never `nullable: true` in v3.x. This affects snapshot content and drift detection thresholds.
