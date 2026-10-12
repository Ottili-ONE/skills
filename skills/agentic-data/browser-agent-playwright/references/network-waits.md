# Network waits — browser-agent-playwright

A fixed `page.waitForTimeout(ms)` is the single most common source of flaky
browser automation: it sleeps whether or not the thing arrived. Playwright's
web-first assertions auto-wait, so use them.

## Wait strategy (ordered — never sleep)
1. `await expect(locator).toBeVisible()` — the element is in the DOM and
   visible. Default timeout 15 s, overridable per assertion.
2. `await expect(locator).toBeEnabled()` — visible *and* not disabled.
3. `await locator.click()` — Playwright auto-waits for the element to be
   actionable (visible, stable, enabled, not covered) before clicking.
4. `await page.waitForURL(url)` — navigation completed.
5. `await page.waitForResponse(resp => resp.url().includes('/api/x'))` — a
   specific network response arrived.
6. `await page.waitForLoadState('domcontentloaded')` — only when waiting for
   the *page* to exist, not for a specific element. `'networkidle'` means no
   more than 0 connections for 500 ms; if a websocket or long-poll stays open,
   `networkidle` never resolves — fall back to `'domcontentloaded'` plus an
   explicit locator wait.

## When `waitForTimeout` is legitimate
Only in tests, for content the test itself injects via `page.setContent(...)`
before the assertion runs. In production code there is no legitimate use.

## Race handling
Two locators racing for the same UI state (e.g. a button *or* a dialog):
```js
await expect(newEmail.or(dialog).first()).toBeVisible();
if (await dialog.isVisible()) { await dialog.accept(); }
```
`locator.or(other).first()` lets web-first assertions wait on either branch.

## Common traps
- Waiting for an element that appears inside an iframe with
  `page.locator(...)` — the locator never finds it. Use
  `page.frameLocator('iframe[src="widget"]').locator(...)`.
- Waiting for `networkidle` on a site with a websocket — the wait times out.
  Use `domcontentloaded` + a locator wait.
- `page.evaluate(() => ...)` does not auto-wait; the result reflects the DOM at
  the instant the script ran, which may be before the element exists.
