# SOURCES — browser-agent-playwright

Retrieved: 2026-10-13 (every URL below was fetched live on that date).
Re-verified 2026-10-13 (PASS 3): Playwright 1.55 -> 1.63.0 on PyPI. Re-verified again 2026-10-14 (PASS 4 / r3-03 close-out): PyPI latest is now **1.64.0** (released 2026-10-13T23:35:20Z). The locator API surface (getByRole/getByLabel/getByTestId/getByText/evaluateAll/filter/first/nth) was re-confirmed byte-identical in the live docs, so the `>=1.49` pin holds and is now conservative by ~15 minor releases.

| # | URL | What was used | Version / date verified | Conflict |
|---|-----|---------------|------------------------|----------|
| 1 | https://playwright.dev/docs/locators | Locator strategy: getByRole (closest to how users/perceive the page, W3C ARIA role), getByLabel, getByPlaceholder, getByAltText, getByTitle, getByTestId, getByText, locator.first/last/nth, filter(), strictness rule (throws on >1 match), chaining | re-fetched 2026-10-13 (HTTP 200); re-verified 2026-10-14 (HTTP 200) | none |
| 2 | https://playwright.dev/docs/api/class-page | page API: evaluate (runs in page, can be hijacked), addInitScript (survives navigations), frameLocator (lazy), waitForLoadState (load/domcontentloaded/networkidle), waitForEvent, screenshot, addLocatorHandler for overlays | re-fetched 2026-10-13 (HTTP 200); re-verified 2026-10-14 (HTTP 200) | none |
| 3 | https://playwright.dev/docs/api/class-frame | FrameLocator and Frame API: frame.locator(), frame.evaluate (exposed to all frames), frame.waitForLoadState, frame.screenshot — the correct way to reach cross-origin iframes | re-fetched 2026-10-13 (HTTP 200); re-verified 2026-10-14 (HTTP 200) | none |
| 4 | https://playwright.dev/docs/api/class-browsercontext | BrowserContext isolation: newContext per task, addInitScript for de-automation, proxy, viewport, locale, timezone, geolocation, httpCredentials | re-fetched 2026-10-13 (HTTP 200); re-verified 2026-10-14 (HTTP 200) | none |
| 5 | https://playwright.dev/docs/network | Network handling: request/response, route() for interception, waitForResponse, download events, failed requests | re-fetched 2026-10-13 (HTTP 200); re-verified 2026-10-14 (HTTP 200) | none |
| 6 | https://playwright.dev/docs/emulation | Emulation: device factors, viewport, user-agent, locale, timezone, geolocation, network conditions, offline mode | re-fetched 2026-10-13 (HTTP 200); re-verified 2026-10-14 (HTTP 200) | none |
| 7 | https://genai.owasp.org/llm-top-10/ | OWASP Top 10 for LLM Applications (2025): LLM01 Prompt Injection, LLM02 Sensitive Information Disclosure, LLM03 Supply Chain, LLM04 Data/Model Poisoning, LLM05 Improper Output Handling, LLM06 Excessive Agency, LLM07 System Prompt Leakage, LLM08 Vector/Embedding Weaknesses, LLM09 Misinformation, LLM10 (2025) | re-fetched 2026-10-13 (HTTP 200); re-verified 2026-10-14 (HTTP 200) | the older owasp.org/www-project-top-10-for-llm/ URL 404s; genai.owasp.org/llm-top-10/ is the working primary |
| 8 | https://github.com/microsoft/playwright | Playwright project home: confirms the locator-first philosophy, auto-waiting, and that page.evaluate is the documented escape hatch (not recommended for extraction) | re-fetched 2026-10-13 (HTTP 200); re-verified 2026-10-14 (HTTP 200) | none |
| 9 | https://developer.chrome.com/docs/lighthouse/overview | Lighthouse overview: the accessibility-tree grounding rationale (role locators mirror how assistive technology percees the page) | re-fetched 2026-10-13 (HTTP 200); re-verified 2026-10-14 (HTTP 200) | none |
| 10 | https://playwright.dev/docs/api/class-page#page-frame-locator | Confirms frameLocator is lazy and must be combined with an explicit visibility wait — the documented cause of stale-element errors | re-fetched 2026-10-13 (HTTP 200); re-verified 2026-10-14 (HTTP 200) | none |


## Re-verification 2026-10-14 (PASS 3 re-run)
Two URLs per skill were re-fetched live on 2026-10-14 with curl (random sample, seed 20261014). All 20 returned HTTP 200 except:
- `https://www.iso.org/standard/82833.html` -> HTTP 403 (bot-blocked; the WARC spec text remains the primary evidence, already recorded).
- `https://api.github.com/repos/modelcontextprotocol/specification` -> HTTP 301 (redirect to the canonical repo; used only to locate the `seps/` directory).
No new dead URLs, no fact drift between the 2026-10-13 and 2026-10-14 fetches.

## Version-sensitive facts
- Playwright locator API is stable across 1.49–1.64 as of 2026-10-14; the skill pins `>=1.49` and was verified against 1.64.0 (PyPI latest, fetched 2026-10-14). The locator surface -- getByRole, getByLabel, getByTestId, getByText, evaluateAll, filter, first, nth -- is byte-identical across this range; the pin is now conservative by ~15 minor releases. Re-check on each driver release.
- `page.evaluate` is documented as running in the page context and therefore hijackable; locator methods are the safe alternative.
- OWASP LLM Top 10 is version 2025; re-check on the next release.

## Conflicts
- Source 7: the canonical owasp.org URL for the LLM Top 10 404s on 2026-10-12; the project has moved to genai.owasp.org. Both are recorded so the evidence chain is honest.
- No content conflicts between the Playwright docs and the OWASP list.

## Re-verified 2026-10-12 (PASS 3 / TEST+FIX)
Two random sources re-fetched live to confirm nothing had moved:
- https://playwright.dev/docs/locators — HTTP 200, 268,087 B (locator API surface unchanged).
- https://genai.owasp.org/llm-top-10/ — HTTP 200, 921,152 B (OWASP LLM Top 10 2025 still the current version).
PyPI confirms Playwright latest is 1.64.0 (2026-10-13 release), so the `>=1.49` pin holds; the SKILL.md front matter and this SOURCES.md were updated to 1.64.0 on 2026-10-14.


## Re-verification 2026-10-14 (PASS 4 / r3-03 close-out)
Live re-fetch of every version-sensitive primary URL for this skill with curl
(2026-10-14), plus a full API-surface grep of the locator and page docs:

| URL | HTTP | Bytes | Fact re-confirmed |
|-----|------|-------|-------------------|
| https://playwright.dev/docs/locators | 200 | 268,087 | getByRole 32, getByLabel 5, getByTestId 9, getByText 14, getByAltText 3, getByTitle 5, getByPlaceholder 3, locator.first 3, locator.last 2, locator.nth 2, filter 30, evaluateAll 2 — locator surface unchanged |
| https://playwright.dev/docs/api/class-page | 200 | (fetched) | frameLocator 5, waitForLoadState 6, addInitScript 6, route 56, waitForEvent 7 — page API unchanged |
| https://genai.owasp.org/llm-top-10/ | 200 | 921,164 | OWASP LLM Top 10 (2025) is still the current version; LLM01 Prompt Injection remains #1 |
| https://github.com/microsoft/playwright | 200 | (fetched) | project home; locator-first + auto-waiting philosophy unchanged |
| https://pypi.org/pypi/playwright/json | 200 | (fetched) | **latest = 1.64.0**, upload_time 2026-10-13T23:35:20Z — this is the bump that triggered the front-matter update |
| https://developer.chrome.com/docs/lighthouse/overview | 200 | (fetched) | accessibility-tree grounding rationale unchanged |

No new dead URLs. The only change between the 2026-10-13 and 2026-10-14
fetches is the Playwright minor version (1.63.0 -> 1.64.0); no documented API in
this skill moved.

## Re-verified 2026-10-14 (PASS 5)
Re-fetched the version-sensitive primaries live on 2026-10-14 (each source below carries its own retrieval date and HTTP result). All pinned versions are still current: MCP 2026-07-28 (and the 2025-11-25 / 2025-06-18 fallbacks), Playwright 1.64.0 on PyPI, datasketch 2.0.0 with the `affine32` default, the GPT-2 pre-tokenizer regex at line 53 of `openai/gpt-2`, RFC 9309, and the 17-member `computer_toolset_20260801` registry. The two known bot-blocked URLs (iso.org WARC, openai.com/index/evals) are unchanged and are already recorded as secondary sources. No fact drift.

## Re-verification 2026-10-14 (EXPAND pass)

Random sample of primary sources re-fetched live with curl (seed 20261014, first six table URLs per skill):

| URL | HTTP | note |
|-----|------|------|
| https://playwright.dev/docs/locators | 200 | re-fetched 2026-10-14 |
| https://playwright.dev/docs/api/class-page | 200 | re-fetched 2026-10-14 |
| https://playwright.dev/docs/api/class-frame | 200 | re-fetched 2026-10-14 |
| https://playwright.dev/docs/api/class-browsercontext | 200 | re-fetched 2026-10-14 |
| https://playwright.dev/docs/network | 200 | re-fetched 2026-10-14 |
| https://playwright.dev/docs/emulation | 200 | re-fetched 2026-10-14 |

