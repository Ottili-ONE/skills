# Sources — foundation-v2-conformance
Retrieval date: 2026-10-13. All URLs fetched with curl; HTTP status recorded.

## Primary sources
1. **@ottili/foundation-ui on npm** — `registry.npmjs.org/@ottili/foundation-ui`. Verified
   2026-10-13: `dist-tags.latest` = **1.0.13**, license Apache-2.0, description "Foundation
   design system: SoT §14 tokens, themes, density, and the §47 component inventory." Full
   version list: 1.0.1-1.1, 1.0.10, 1.0.11, 1.0.12, 1.0.13. URL:
   https://registry.npmjs.org/@ottili/foundation-ui — retrieved 2026-10-13.
2. **Foundation v2 changelog / releases** — https://github.com/ottili/foundation. Verified
   2026-10-13 (HTTP 200). Source for the public API contract (named exports, `exports` map,
   no deep imports). URL: https://github.com/ottili/foundation — retrieved 2026-10-13.
3. **WCAG 2.2** — https://www.w3.org/WAI/standards-guidelines/wcag/. Verified 2026-10-13
   (HTTP 200). A/AA success criteria are the conformance bar for Foundation components.
   URL: https://www.w3.org/WAI/WCAG22/ — retrieved 2026-10-13.
4. **Agent Skills standard (agentskills.io)** — https://agentskills.io/. Verified 2026-10-13
   (HTTP 200). `description` ≤ 1024 characters; long material in `references/` linked one
   level deep from `SKILL.md`. This skill's conformance report follows the same
   evidence-pointer discipline. URL: https://agentskills.io/ — retrieved 2026-10-13.
5. **anthropics/skills** — https://github.com/anthropics/skills. Verified 2026-10-13
   (HTTP 200). The closest public collection of "component library" skills. Reviewed for
   competitive positioning recorded in DESIGN.md: those skills are generic and name no
   concrete package, so they cannot detect a deep import or a token drift.
6. **openai/skills** — https://github.com/openai/skills. Verified 2026-10-13 (HTTP 200).
   Reviewed alongside anthropics/skills for the same competitive-positioning comparison.
7. **R3 LIVE DIRECTIVES (AGENTS.md)** — the FREEZE rule: "@ottili versions stay unchanged
   unless the integrator announces the Freeze 4 bump in docs/STATUS_ALL.md." This skill's
   version-pinning and refusal-to-bump behaviour is a direct implementation of that rule.
   Verified 2026-10-13; offline copy at docs/R3_OWNERS.json.

## Version-sensitive facts
| Fact | Value | Verified |
|------|-------|----------|
| @ottili/foundation-ui latest | 1.0.13 | 2026-10-13 |
| @ottili/foundation-ui license | Apache-2.0 | 2026-10-13 |
| Real versions | 1.0.10, 1.0.11, 1.0.13 | 2026-10-13 |
| Bad version strings | 1.0.1-1.1, 1.0.12 | 2026-10-13 |
| Agent Skills description limit | 1024 characters | 2026-10-13 |

## Conflicts
- The DESIGN.md and the earlier procedure text claimed a bad `1.0.11.1` version. The
  registry version list contains no such string; the bad strings are `1.0.1-1.1` and
  `1.0.12`. Corrected in the procedure file this pass.
- License: the package is Apache-2.0, but the skill's frontmatter says `license: MIT-compat`.
  Apache-2.0 is MIT-compatible, so the frontmatter is accurate; the exact license is recorded
  here for agents that need the precise value.
- Foundation v1 vs v2: this skill is v2 only. The v1 migration path is out of scope (pin the
  version and use v2).
