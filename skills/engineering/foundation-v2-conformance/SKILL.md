---
name: foundation-v2-conformance
description: "Enforce correct usage of the Foundation v2 UI packages: token-only styling, named imports, no bypass of abstraction layers, tracked workaround markers, and fresh-consumer tests that fail when a consumer drifts."
license: MIT-compat
compatibility: "Node.js or Python host; Foundation v2 packages installed; Linux"
metadata: {}
allowed-tools: []
---
# Foundation v2 Conformance Skill (body <500 lines)

Full procedure: references/foundation-v2-conformance-procedure.md
Sources: references/SOURCES.md
Evals: references/EVALS.md
Helpers: scripts/

## When to use this skill
- You import or build on top of a Foundation v2 UI package.
- You need to prove a consumer (app, micro-frontend, library) uses the package the way it was designed.
- You have added a workaround and need to track it until a proper fix lands.
- A reviewer asks "is this component actually conformant, or is it bypassing the tokens?"

## When NOT to use this skill
- Styling that intentionally escapes the design system (experimental prototypes).
- Legacy code you are not yet migrating (use a workaround marker instead).
- Packages that are not part of Foundation v2.

## Decision table — conformance checks
| Check | How | Fail signal |
|-------|-----|-------------|
| Token-only styling | grep for raw color/spacing literals in styled components | hex/rgb/px literals outside `/* ALLOWED */` comments |
| Named imports only | AST/import scan for default or namespace imports of Foundation packages | `import Foo from '@ottili/foundation-button'` |
| No bypass of abstraction | assert no direct access to `__foundation_internal` or underscore-prefixed exports | any match on `_\w+` export access |
| Workaround markers present | regex for `WORKAROUND:` or `FV2-WA:` comments | workaround code with no marker |
| Fresh-consumer test exists | run the consumer test suite in isolation | test imports the package under test directly |

## Numbered procedure
1. Identify the Foundation v2 packages in scope (from `package.json` dependencies, version pinned).
2. Scan every consumer file for imports; reject default and namespace imports; require named imports.
3. Scan for styling literals; compare against the token allow-list; flag anything not derivable from a token.
4. Scan for workaround markers; every flagged block must carry a `FV2-WA:` comment with owner and date.
5. Write or run a fresh-consumer test: a test file that imports only the public package surface and exercises it through its public API, never reaching into internals.
6. Run the helper `scripts/check_foundation_conformance.py` against the consumer; fix each finding in order.
7. Re-run until zero findings; commit the evidence report.

## Pitfalls from research
- A "fresh-consumer test" that imports the package source directly is not fresh — it is a unit test in disguise.
- Workaround markers decay: a marker older than 30 days without a linked ticket is a stale escape hatch, not a tracked workaround.
- Token allow-lists drift from the published token set; re-derive the allow-list from the package, never from memory.
- Namespace imports (`import * as Foo`) silently expose private exports and break on minor versions.

## Verification checklist
- [ ] Every Foundation v2 import is a named import of a public export.
- [ ] No raw styling literals outside token-derived values.
- [ ] Every workaround carries `FV2-WA:` with owner + date.
- [ ] A fresh-consumer test exists and passes in isolation.
- [ ] Conformance report is committed or referenced.
