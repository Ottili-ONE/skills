# Procedures — browser-agent-playwright

Verified 2026-10-08 against Playwright docs (playwright.dev/docs/api/class-page,
playwright.dev/docs/locators). Version-sensitive: API stable across 1.49–1.55;
re-check on each driver release.

## 1. Locator strategy (ordered)
1. `page.getByRole('button', { name: 'Submit' })` — role + accessible name.
2. `page.getByLabel('Email')` — form fields.
3. `page.getByTestId('save-btn')` — data-testid hooks the team controls.
4. `page.getByText('Submit', { exact: true })` — only as fallback.
5. CSS/XPath — last resort; brittle to markup changes.

Good (specific):
```js
const save = page.getByRole('button', { name: 'Save' });
await expect(save).toBeEnabled();
await save.click();
```
Bad (fragile):
```js
await page.click('button.blue > span.icon');          // markup change kills it
await page.waitForTimeout(2000);                      // flaky
await page.evaluate(() => document.querySelector('.x').click());
```

## 2. Frame handling
- Always start from `page.mainFrame()`.
- For iframes: `frame = page.frame('checkout')` or `page.frameLocator('iframe[src*="widget"]')`.
- `frame.getByRole(...)` works inside the frame; never use top-level `page` for inside-frame elements.

## 3. Network waits
- `await page.goto(url, { waitUntil: 'networkidle' })` for full load.
- For SPA route changes: `await page.waitForURL(/dashboard/)` then `await expect(...).toBeVisible()`.
- For API-driven content: wait on the locator that depends on the API, not a timeout.

## 4. Extraction
```js
const title = await page.title();
const rows = await page.getByRole('row').evaluateAll els => els.map(e => e.textContent));
```
Never `page.evaluate(() => document.body.innerHTML)` — it returns untrusted markup that
becomes prompt content (see injection-defense.md).

## 5. Download / upload
- Downloads: `page.on('download', async dl => { const path = await dl.path(); ... })`.
- Uploads: `locator.setInputFiles([...])`.

## 6. Error recovery
- Stale element: re-query the locator (locators are live references).
- Timeout: capture a screenshot + console errors for the report: `await page.screenshot({ path: 'fail.png' })` and `page.on('console', msg => ...)`.

## 7. Clean shutdown
```js
try {
  // ... task
} finally {
  await context.close();
}
```
