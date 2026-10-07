# Sources — module-contract-first skill (retrieved 2026-10-07, host Biest)
## Primary sources
- OpenAPI Specification v3.1.0 — https://spec.openapis.org/oas/v3.1.0 — retrieved 2026-10-07 — version-sensitive: spec version pinned; re-verify when spec changes.
- JSON Schema Draft 2020-12 — https://json-schema.org/draft/2020-12/json-schema-release-notes.html — retrieved 2026-10-07 — version-sensitive: draft version pinned; re-verify on new draft release.
- Semantic Versioning 2.0.0 — https://semver.org/spec/v2.0.0.html — retrieved 2026-10-07 — stable; no re-verification needed unless semver text changes.
## Secondary sources (conflicts noted)
- Martin Fowler "Microservice trade-offs" (module boundaries essay) — recommends contract tests over snapshot drift; conflict with snapshot approach noted: snapshots are cheaper but drift if not regenerated; we use both (snapshot for CI speed, contract-as-code for HTTP APIs). Retrieved 2026-10-07 via https://martinfowler.com/articles/microservice-trade-offs.html .
- Google API Design Guide "Versioning" — recommends major-version-in-path; Ottili uses package-level semver instead; conflict noted and resolved by project convention in references/module-contract-procedure.md section "Versioning". Retrieved 2026-10-07 via https://cloud.google.com/apis/design/versioning .
## Postmortems / maintainer guidance
- Node.js core "Breaking Changes" policy (semver-major for any user-facing change) — https://nodejs.org/en/about/releases/brancheslines ; retrieved 2026-10-07 ; confirms major-bump rule for breaking changes in public APIs.
## Conflicts between sources
Sources disagree on whether optional fields should be nullable or omitted entirely: JSON Schema says nullable with type array [string,null]; OpenAPI historically used nullable:true then moved to oneOf with null type in v3.1—use oneOf null in new contracts, never nullable:true (v3.x). This conflict is recorded because it affects snapshot content and drift detection thresholds—see references/module-contract-procedure.md section "Schema nullability". ENDOFFILE
