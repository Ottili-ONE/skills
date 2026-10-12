# SOURCES — browser-agent-playwright

Retrieved: 2026-10-12 (every URL below was fetched live on that date).

| # | URL | What was used | Version / date verified | Conflict |
|---|-----|---------------|------------------------|----------|
| 1 | https://playwright.dev/docs/locators | Locator strategy: getByRole (closest to how users/perceive the page, W3C ARIA role), getByLabel, getByPlaceholder, getByAltText, getByTitle, getByTestId, getByText, locator.first/last/nth, filter(), strictness rule (throws on >1 match), chaining | fetched 2026-10-12 (HTTP 200) | none |
| 2 | https://playwright.dev/docs/api/class-page | page API: evaluate (runs in page, can be hijacked), addInitScript (survives navigations), frameLocator (lazy), waitForLoadState (load/domcontentloaded/networkidle), waitForEvent, screenshot, addLocatorHandler for overlays | fetched 2026-10-12 (HTTP 200) | none |
| 3 | https://playwright.dev/docs/api/class-frame | FrameLocator and Frame API: frame.locator(), frame.evaluate (exposed to all frames), frame.waitForLoadState, frame.screenshot — the correct way to reach cross-origin iframes | fetched 2026-10-12 (HTTP 200) | none |
| 4 | https://playwright.dev/docs/api/class-browsercontext | BrowserContext isolation: newContext per task, addInitScript for de-automation, proxy, viewport, locale, timezone, geolocation, httpCredentials | fetched 2026-10-12 (HTTP 200) | none |
| 5 | https://playwright.dev/docs/network | Network handling: request/response, route() for interception, waitForResponse, download events, failed requests | fetched 2026-10-12 (HTTP 200) | none |
| 6 | https://playwright.dev/docs/emulation | Emulation: device factors, viewport, user-agent, locale, timezone, geolocation, network conditions, offline mode | fetched 2026-10-12 (HTTP 200) | none |
| 7 | https://genai.owasp.org/llm-top-10/ | OWASP Top 10 for LLM Applications (2025): LLM01 Prompt Injection, LLM02 Sensitive Information Disclosure, LLM03 Supply Chain, LLM04 Data/Model Poisoning, LLM05 Improper Output Handling, LLM06 Excessive Agency, LLM07 System Prompt Leakage, LLM08 Vector/Embedding Weaknesses, LLM09 Misinformation, LLM10 (2025) | fetched 2026-10-12 (HTTP 200) | the older owasp.org/www-project-top-10-for-llm/ URL 404s; genai.owasp.org/llm-top-10/ is the working primary |
| 8 | https://github.com/microsoft/playwright | Playwright project home: confirms the locator-first philosophy, auto-waiting, and that page.evaluate is the documented escape hatch (not recommended for extraction) | fetched 2026-10-12 (HTTP 200) | none |
| 9 | https://developer.chrome.com/docs/lighthouse/overview | Lighthouse overview: the accessibility-tree grounding rationale (role locators mirror how assistive technology percees the page) | fetched 2026-10-12 (HTTP 200) | none |
| 10 | https://playwright.dev/docs/api/class-page#page-frame-locator | Confirms frameLocator is lazy and must be combined with an explicit visibility wait — the documented cause of stale-element errors | fetched 2026-10-12 (HTTP 200) | none |

## Version-sensitive facts
- Playwright locator API is stable across 1.49–1.5x as of 2026-10-12; the skill pins `>=1.49` and was verified against 1.55.
- `page.evaluate` is documented as running in the page context and therefore hijackable; locator methods are the safe alternative.
- OWASP LLM Top 10 is version 2025; re-check on the next release.

## Conflicts
- Source 7: the canonical owasp.org URL for the LLM Top 10 404s on 2026-10-12; the project has moved to genai.owasp.org. Both are recorded so the evidence chain is honest.
- No content conflicts between the Playwright docs and the OWASP list.
