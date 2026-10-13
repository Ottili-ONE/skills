# Module Contract First — Full Procedure
Retrieval date: 2026-10-12. Host: Biest. SEARCH_ENDPOINT none (URLs fetched directly).

## Verified tool versions
- `scripts/check_contract_drift.py` (this repo): v1, offline deterministic, verified on Biest 2026-10-12.
- OpenAPI v3.1.0: https://spec.openapis.org/oas/v3.1.0 — retrieved 2026-10-12.
- JSON Schema Draft 2020-12: https://json-schema.org/draft/2020-12/json-schema-release-notes.html — retrieved 2026-10-12.
- SemVer 2.0.0: https://semver.org/spec/v2.0.0.html — retrieved 2026-10-12.

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
$ python3 scripts/check_contract_drift.py --enumerate src/users
ok: enumerated 14 symbols -> src/users/module-contracts/users.json
$ cat src/users/module-contracts/users.json
{"symbols": ["create_user", "delete_user", "get_user", ...]}
```

## Step 2 — Check for drift
```bash
python3 scripts/check_contract_drift.py --check <module-dir>
```
Exit 0 means the live surface matches the snapshot. Any added/removed/renamed public symbol prints `DRIFT DETECTED` and exits non-zero. On intentional change, re-run `--enumerate` and commit the new snapshot in the same PR.

## Step 3 — Check for import cycles
```bash
python3 scripts/check_contract_drift.py --cycles <module-dir>
```
Detects cycles in the module's import graph. Break a cycle by extracting shared types into an internal-only module that both depend on.

## Contract-first rules
- A *public contract* is any exported symbol, endpoint, or message schema that another module consumes.
- Changing a contract is a breaking change unless the version is bumped (SemVer 2.0.0: bump MAJOR for breaking, MINOR for additive, PATCH for fixes only).
- Internal helpers (leading underscore) are not part of the contract and may change freely.
- A module boundary is the set of files under one directory; do not reach across a boundary except through the contract.
- Drift tests run in CI on every PR; they are not optional.

## Pitfalls from research
- Hand-edited snapshots silently lie: always regenerate with `--enumerate`.
- A renamed export is a *removal + addition*, not a rename — the drift checker shows both.
- Additive changes still require a MINOR bump; "it is backwards compatible" is not a free pass.
- A cycle that spans modules is a design failure, not a lint warning.

## Verification checklist
- [ ] Every module has a committed `module-contracts/<module>.json` snapshot.
- [ ] `--check` passes on the current tree.
- [ ] `--cycles` reports no cycles across module boundaries.
- [ ] Every contract change in a PR is accompanied by a version bump or an explicit breaking-change note.
