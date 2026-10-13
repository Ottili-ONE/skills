# DESIGN — module-contract-first

## Trigger description (draft)
Fires when: an agent must define the public contract of a module before implementing it; when a
PR changes a public function signature, an exported type, or an API response; when a drift test
fails; or when four agents share one working tree and need a boundary that prevents cross-module
breakage. Does NOT fire for: private helpers inside a module, or generated code with no public API.

## What it does better than existing public skills
OpenAPI and JSON Schema docs teach *how to describe* a contract; they do not teach the
contract-first workflow for a multi-agent tree. This skill fixes the workflow: write the contract
YAML before any implementation, snapshot it into `module-contracts/<module>.snap` at the point
the implementation lands, and run `scripts/check_contract_drift.py` in CI so a snapshot that
diverges from the implementation fails the build. It also defines the boundary rules (one module
imports another only through its public contract; no deep imports; no shared mutable state across
modules) and records the real incident: a snapshot was regenerated "to make CI green" and hid a
breaking change for two weeks, because the snapshot was treated as documentation rather than as a
test oracle.

## Procedure outline
1. For each module, write `module-contracts/<module>.yaml`: name, version, exported functions,
   types, and HTTP endpoints with request/response JSON Schema.
2. Implement against the contract; never change a public signature without a major version bump.
3. Snapshot: `scripts/check_contract_drift.py --snapshot` writes `module-contracts/<module>.snap`
   from the live code; the committed snapshot is the baseline.
4. CI: `scripts/check_contract_drift.py --check` compares the committed snapshot to the live code;
   any divergence is a FAIL.
5. Boundaries: a module may import another module's *public* entry point only; deep imports
   (e.g. `../internal/helper`) are a defect.
6. Versioning: semver major for any breaking change; the contract file carries the version, and
   the package.json must match.

## Scripts planned
- `scripts/check_contract_drift.py` — snapshot and check modes; exits 0 on match, 1 on drift.

## Five eval prompts
1. "Add a function `getUser(id)` to the billing module." → agent must first add it to the
   contract YAML with its signature and types, then implement, then snapshot.
2. "The drift test failed: `GET /users` now returns `email`." → agent must either update the
   contract (breaking → major bump) or revert the change; silently regenerating the snapshot is
   forbidden.
3. "Module A imports `from billing/internal/pricing.js`." → agent must reject the deep import
   and route through the public entry point.
4. "Should I bump billing from 1.4.2 to 1.5.0 for an added optional field?" → no breaking change;
   minor bump is correct; the contract gains an optional field.
5. "Four agents are editing the same module." → agent must check that each edit touches only its
   owned paths and that the contract snapshot is regenerated only by the owner.
