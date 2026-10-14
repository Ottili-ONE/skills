# Sources — playwright-a11y-e2e
Retrieval date: 2026-10-14 (re-verified). All URLs fetched with curl; HTTP status recorded.

## Primary sources
1. **@axe-core/playwright** — `registry.npmjs.org/@axe-core/playwright`. Verified 2026-10-13:
   `dist-tags.latest` = **4.13.0** (previous SOURCES entry said 4.9.x — stale; corrected here).
   The adapter injects axe-core into the page and returns `violations`/`incomplete`/`passes`
   arrays. URL: https://registry.npmjs.org/@axe-core/playwright — retrieved 2026-10-13.
2. **axe-core** — `registry.npmjs.org/axe-core`. Verified 2026-10-13: latest = **4.14.0**.
   Rule list lives at https://github.com/dequelabs/axe-core/blob/develop/doc/rule-descriptions.md
   — retrieved 2026-10-13 (raw 200).
3. **Playwright** — `registry.npmjs.org/playwright`. Verified 2026-10-14: `dist-tags.latest` = **1.64.0**. The browser automation library; `@playwright/test` is the test runner. URL: https://www.npmjs.com/package/playwright — retrieved 2026-10-14.
3a. **Playwright Page API** — https://playwright.dev/docs/api/class-page. Verified 2026-10-13
   (HTTP 200, ~975 KB). `page.viewportSize`, `page.keyboard`, `page.goto`, `page.locator`,
   `page.screenshot` are the primitives this skill uses. Version-agnostic; the skill targets
   Playwright 1.50+ (verified against the docs landing page, which is the current channel).
4. **WCAG 2.2** — https://www.w3.org/WAI/standards-guidelines/wcag/. Verified 2026-10-13
   (HTTP 200). A/AA success criteria are the pass/fail bar; the Understanding pages are the
   authoritative interpretation. URL: https://www.w3.org/TR/WCAG22/ — retrieved 2026-10-13.
5. **MDN ARIA forms guidance** — https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/forms.
   Verified 2026-10-13 (HTTP 200). Source for "form controls need accessible names" and
   keyboard operability requirements.
6. **Deque axe-core docs** — https://www.deque.com/axe/. Verified 2026-10-13 (HTTP 200).
   axe-core rule taxonomy and the `impact` field (`critical`, `serious`, `moderate`, `minor`).

## Version-sensitive facts
| Fact | Value | Verified |
|------|-------|----------|
| @axe-core/playwright latest | 4.13.0 | 2026-10-14 |
| axe-core latest | 4.14.0 | 2026-10-14 |
| Playwright latest | 1.64.0 | 2026-10-14 |

| axe report keys | `violations`, `incomplete`, `passes` | 4.10+ (4.13.0 confirmed) |
| WCAG conformance level | A, AA, AAA | WCAG 2.2, retrieved 2026-10-13 |

## Conflicts / corrections
- The earlier SOURCES entry claimed axe-core 4.9.x. The registry returns 4.14.0 as latest and
  4.13.0 as the latest @axe-core/playwright. The skill's `SEVERITY_TAGS` set
  (`violations`, `incomplete`) is unchanged across 4.9–4.14, so the checker is unaffected; only
  the version claim is corrected.
- axe-core 4.14.0 (released 2026-10-05 per the registry `time` field) introduced new rules; a rule that passes today may fail after an axe upgrade.
  Re-fetch `registry.npmjs.org/axe-core` before any axe-version bump and record the new rule
  names in this file.
