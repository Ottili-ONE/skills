# Foundation v2 Conformance — Full Procedure
Retrieval date: 2026-10-13. Sources: npmjs.com/@ottili/foundation-ui (latest 1.0.13);
github.com/ottili/foundation; w3.org/WAI/WCAG22/. Verified versions below are snapshots as
of the retrieval date. Re-fetch on version-bump announcements in docs/STATUS_ALL.md
(Freeze channel only; per R3 FREEZE rule, never bump @ottili versions without integrator
approval).

## Verified versions
| Artifact | Version | Verified | Note |
|----------|---------|----------|------|
| @ottili/foundation-ui | 1.0.13 | 2026-10-13 | `dist-tags.latest` from registry.npmjs.org |
| @ottili/foundation-button | (part of foundation-ui) | 2026-10-13 | pinned with foundation-ui |
| @ottili/foundation-tokens | (part of foundation-ui) | 2026-10-13 | token file is the allow-list source |

Corruption history (do not install): `1.0.1-1.1` and `1.0.12` are bad version
strings that appear in the registry version list but are not real releases. Only 1.0.10,
1.0.11, 1.0.13 are real; 1.0.13 is latest. (Verified 2026-10-13 against the full version
list; the earlier claim of a `1.0.11.1` bad version was a typo and is corrected here.)

## Procedure
1. Pin the Foundation package versions in package.json with an exact `1.0.13` (no `^`, no
   `~`) in any locked-release lane. The FREEZE rule forbids bumping without integrator
   approval recorded in docs/STATUS_ALL.md.
2. Import components and tokens from the package entry point only. Never import a deep path
   such as `@ottili/foundation-ui/dist/index`; the package `exports` map is the contract.
3. Use the token set for spacing, type, and colour. A raw value that is not in the token
   file is a defect, not a workaround. Re-derive the allow-list from the published token
   file on every run; never from memory.
4. Mark workarounds explicitly with a `data-ottili-workaround` attribute and a comment
   naming the ticket (e.g. `FV2-WA: ISSUE-1234`). A workaround older than 30 days without
   a linked ticket is a stale escape hatch, not a tracked workaround.
5. Run the fresh-consumer test: a minimal app that imports the component and renders it
   with only the documented props. If it fails, the public API has drifted. A test that
   imports the package source directly is a unit test in disguise, not a fresh-consumer
   test.
6. Record conformance in the component's test file with the exact Foundation version
   asserted.

## Conformance checks (run in order)
| Check | How | Fail signal |
|-------|-----|-------------|
| Token-only styling | grep for raw color/spacing literals in styled components | hex/rgb/px literals outside `/* ALLOWED */` comments |
| Named imports only | AST/import scan for default or namespace imports of Foundation packages | `import Foo from '@ottili/foundation-button'` |
| No bypass of abstraction | assert no direct access to `__foundation_internal` or underscore-prefixed exports | any match on `_\w+` export access |
| Workaround markers present | regex for `FV2-WA:` comments | workaround code with no marker |
| Fresh-consumer test exists | run the consumer test suite in isolation | test imports the package under test directly |

## Scripts (shipped)
- `scripts/check_foundation_tokens.py` — validates that every raw design value used in
  CSS/JS resolves to a token in the Foundation token file. Exit 0 = all token-derived;
  exit 1 = findings. Lines carrying an `ALLOWED` comment marker naming a ticket are exempt
  (the workaround escape hatch). Deterministic, no network.
- `scripts/check_foundation_tokens_test.py` — offline self-tests (good/dirty/allowed files).
- `scripts/fresh_consumer_test.sh <component> <outdir>` — builds a throwaway app that imports
  a named Foundation component and asserts it renders with documented props only. A test
  that reaches into `dist/` or `__foundation_internal` fails here. Foreground only.

## Verification checklist (all must pass before merge)
- [ ] Every Foundation v2 import is a named import of a public export.
- [ ] No raw styling literals outside token-derived values.
- [ ] Every workaround carries `FV2-WA:` with owner + date.
- [ ] A fresh-consumer test exists and passes in isolation.
- [ ] Conformance report is committed or referenced.
