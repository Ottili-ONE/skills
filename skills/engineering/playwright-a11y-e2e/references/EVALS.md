# Playwright A11y E2E — EVALS

Each prompt is a realistic request an agent would receive. Expected behaviour shows what the
skill should produce; failure signs show what would indicate the skill did not fire or misfired.

## 1. "Write a test that clicks the save button."
- Expected: agent uses `page.getByTestId('save')`. A test using `page.locator('.btn-primary')`
  or `page.getByText('Save')` for a non-unique string is a defect.
- Failure signs: CSS class, XPath, or text-based selector; test passes while checking the wrong element.
**What the skill changes vs no skill**: without the skill an agent writes `page.locator(".btn-primary").click()` and the test keeps passing while checking the wrong element, so a refactor renames the class and the test goes green on a broken page. The skill makes `getByTestId`/`getByRole` the only allowed selectors, so a selector that breaks on refactor is a defect, not a passing test.

## 2. "axe reports a critical contrast violation."
- Expected: agent keeps the rule id + a screenshot in the evidence artifact and fixes the token,
  never lowers the assertion.
- Failure signs: assertion weakened to "no critical" without a screenshot; rule id not recorded.
**What the skill changes vs no skill**: without the skill an agent lowers the axe assertion to "no critical" and ships. The skill keeps every rule id in the evidence artifact and never weakens the assertion, so a contrast regression is recorded with its rule id instead of being argued away.

## 3. "Tab through the modal and check keyboard behaviour."
- Expected: agent asserts focus moves into the modal, the last element wraps to the first, and
  Esc closes it; no keyboard trap.
- Failure signs: no tab-order assertion; modal opened but focus stayed on the page behind it.
**What the skill changes vs no skill**: without the skill an agent asserts only that the modal opens. The skill forces a keyboard traversal that asserts focus moves into the modal, the last element wraps to the first, Esc closes it and there is no trap, so a focusable-but-unreachable control is caught.

## 4. "The menu breaks at 320 but passes at 1440."
- Expected: agent adds the 320 breakpoint and asserts no horizontal scroll and that the primary
  CTA is visible without scrolling.
- Failure signs: responsive check only at one breakpoint; horizontal scroll not asserted.
**What the skill changes vs no skill**: without the skill an agent checks only at 1440px. The skill makes the breakpoint loop (320/768/1024/1440) and the horizontal-scroll assertion the contract, so a mobile regression is reproduced instead of missed.

## 5. "The test uses `waitForTimeout(500)`."
- Expected: agent replaces it with an explicit wait on the testid or load state.
- Failure signs: `waitForTimeout` left in place — it is a flake factory.
**What the skill changes vs no skill**: without the skill an agent leaves `waitForTimeout(500)` in place and calls it stable. The skill replaces it with an explicit wait on the testid or load state, so a flake factory is not a passing test.

## Worked examples

**Good selector + axe evidence**:
```js
const save = await page.getByTestId('save');
await save.click();
const axe = await runAxe(page);
expect(axe.violations.filter(v => v.impact === 'critical')).toHaveLength(0);
// evidence artifact: axe.json records every rule id, not just "0 critical"
```
**Bad selector** (passes while checking the wrong element):
```js
await page.locator('.btn-primary').click(); // breaks on every refactor
```
**Good keyboard traversal** (reaches shadow DOM):
```js
for (const el of await page.locator('*').elementHandles()) {
  const shadow = await el.evaluate(e => e.shadowRoot);
  if (shadow) await shadow.querySelectorAll('button')[0]?.focus();
}
```
**Bad responsive check** (only 1440px):
```js
await page.setViewportSize({ width: 1440, height: 900 });
// misses every mobile regression; the loop must include 320/768/1024/1440
```

## Verification checklist
- [ ] Every selector is a data-testid
- [ ] axe run on every navigated page, zero critical/serious
- [ ] Tab order asserted at each breakpoint
- [ ] Evidence artifact kept on failure (screenshot + axe JSON)

## Near-miss prompts (act before the incident)
- **N1 — "The axe scan is green, so the page is accessible."** Answer: no. Green axe means zero *reported* violations, not that every control is reachable; run the keyboard check too.
- **N2 — "Use `:focus-visible` as the WCAG criterion."** Answer: no. `:focus-visible` is a CSS pseudo-class, not a WCAG success criterion; assert focus order and focusable state instead.
- **N3 — "nth-child or a class selector is fine, the test passes."** Answer: no. Those selectors break on every refactor; use `getByTestId`, then `getByRole`/`getByLabel`.
- **N4 — "The axe run on a dynamic modal without waiting for `aria-hidden=false`."** Answer: no. You get false violations or missed violations; wait for the state change before scanning.
- **N5 — "Responsive check only at 1440."** Answer: no. The loop must include 320px, 768px, 1024px and 1440px; mobile bugs are never caught otherwise.
- **N6 — "Keyboard tests that skip shadow DOM."** Answer: no. They fail silently on Web Components; traverse the shadow root.
- **N7 — "The screenshot proves it's accessible."** Answer: no. A screenshot is evidence of rendering, not of keyboard reachability; pair it with the axe JSON and the tab-order assertion.
- **N8 — "I'll weaken the axe rule list to 'no critical'."** Answer: no. Weakened assertions are how a regression ships silently; keep every rule id in the evidence artifact.
- **N9 — "The test only runs on desktop, mobile is out of scope."** Answer: no. The breakpoint loop must include 320px; a mobile-only regression is exactly what the loop exists to catch.
- **N10 — "The evidence artifact can just be the console log."** Answer: no. The artifact must be the axe JSON (every rule id) plus the screenshot and the tab-order assertion; a console log cannot be re-scanned.
