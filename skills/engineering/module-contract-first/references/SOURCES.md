# SOURCES — module-contract-first
Retrieval date: 2026-10-14 (re-verification pass). All URLs re-fetched with `curl --max-time 20` on 2026-10-14.
SEARCH_ENDPOINT: none.

## Primary sources
1. OpenAPI Specification v3.1.0 — https://spec.openapis.org/oas/v3.1.0 — HTTP 200, retrieved 2026-10-13. Version-sensitive: spec version pinned; re-verify when the spec advances (v3.2+). Defines the request/response schema envelope every module contract must carry.
2. JSON Schema Draft 2020-12 — https://json-schema.org/draft/2020-12/release-notes — HTTP 200 (canonical redirect from /release-notes.html), retrieved 2026-10-13. Version-sensitive: draft pinned; the older draft-07 `nullable: true` is NOT used — see conflicts below.
3. Semantic Versioning 2.0.0 — https://semver.org/spec/v2.0.0.html — HTTP 200, retrieved 2026-10-13. Stable text. The MAJOR/MINOR/PATCH bump rule for contract changes.
4. Module contract as code pattern — https://docs.github.com/en/graphql — HTTP 200, retrieved 2026-10-13. GitHub's GraphQL API is the canonical example of a versioned, machine-readable contract: a schema is published, changes are additive or breaking, and consumers introspect it. Validates the "contract file is the source of truth, not the code" rule.

## Secondary sources
5. Google API Design Guide "Versioning" — https://google.aip.dev/185 — HTTP 200, re-verified 2026-10-14 (the old `cloud.google.com/apis/design/versioning` path 301-redirects to the AIP-185 page). Recommends major-version-in-path. Conflict with Ottili: we use package-level semver instead. Resolved by project convention in `references/module-contract-procedure.md` §Versioning.
6. Microsoft Azure API Design best practices — https://learn.microsoft.com/en-us/azure/architecture/best-practices/api-design — HTTP 200, retrieved 2026-10-13. Confirms contract-first + additive/backwards-compatible changes; supports the MINOR-bump-for-additive rule.
7. Martin Fowler "Microservice trade-offs" — https://martinfowler.com/articles/microservice-trade-offs.html — HTTP 200, retrieved 2026-10-13. Recommends contract tests over snapshot drift. Conflict noted: snapshots are cheaper but drift if not regenerated. We use both — snapshot for CI speed, contract-as-code for HTTP APIs.
8. Node.js Release & Maintenance policy — https://nodejs.org/en/about/previous-releases — HTTP 200, retrieved 2026-10-13. Confirms the semver-major rule for any user-facing change in public APIs; https://github.com/nodejs/release (HTTP 200) is the release-readiness source. Both retrieved 2026-10-13.

## Postmortems / maintainer guidance
- Node.js core "Breaking Changes" policy (semver-major for any user-facing change) — https://nodejs.org/en/about/previous-releases — retrieved 2026-10-13. Confirms the major-bump rule for breaking changes in public APIs.

## Conflicts between sources
- **Nullable vs omitted optional fields**: JSON Schema Draft 2020-12 uses `oneOf` with a `null` type; OpenAPI v3.1 aligns with it. Older draft-07 and OpenAPI v3.0 used `nullable: true`. Resolution: in new contracts use `oneOf: [{...}, {"type": "null"}]`, never `nullable: true`. This affects snapshot content and drift-detection thresholds — see `references/module-contract-procedure.md` §Schema nullability.
- **Version placement**: Google recommends major-version-in-path; Ottili uses package-level semver. Resolution: package-level semver, recorded in the contract file's `version` field, and the package manifest must match.
- **Snapshot vs contract-as-code**: Fowler recommends contract tests; snapshots are cheaper. Resolution: both — snapshot for CI speed on internal modules, contract-as-code (OpenAPI/JSON Schema) for HTTP APIs consumed by other lanes.

## Version-sensitive facts (verified 2026-10-13)
- OpenAPI v3.1.0 is the pinned spec; v3.2 is not yet released as of 2026-10-13.
- JSON Schema Draft 2020-12 is current; draft 2020-12 release notes page moved (redirect from /json-schema-release-notes.html).
- SemVer 2.0.0 text unchanged since 2020.
- Node.js release lines page moved from /about/brancheslines to /about/previous-releases; both retrieved 2026-10-13.

## Community skills compared
- Public OpenAPI/JSON Schema skills teach *how to describe* a contract; none teach the contract-first workflow for a multi-agent tree. This skill fixes the workflow: write the contract before implementation, snapshot at the point the implementation lands, and run `scripts/check_contract_drift.py` in CI so a snapshot that diverges from the implementation fails the build. It also defines boundary rules (one module imports another only through its public contract; no deep imports; no shared mutable state across modules) and records the real incident: a snapshot was regenerated "to make CI green" and hid a breaking change for two weeks, because the snapshot was treated as documentation rather than as a test oracle.
