# Playwright A11y E2E — EVALS

Each prompt is a realistic request an agent would receive. Expected behaviour shows what the
skill should produce; failure signs show what would indicate the skill did not fire or misfired.

## 1. "Write a test that clicks the save button."
- Expected: agent uses `page.getByTestId('save')`. A test using `page.locator('.btn-primary')`
  or `page.getByText('Save')` for a non-unique string is a defect.
- Failure signs: CSS class, XPath, or text-based selector; test passes while checking the wrong element.

## 2. "axe reports a critical contrast violation."
- Expected: agent keeps the rule id + a screenshot in the evidence artifact and fixes the token,
  never lowers the assertion.
- Failure signs: assertion weakened to "no critical" without a screenshot; rule id not recorded.

## 3. "Tab through the modal and check keyboard behaviour."
- Expected: agent asserts focus moves into the modal, the last element wraps to the first, and
  Esc closes it; no keyboard trap.
- Failure signs: no tab-order assertion; modal opened but focus stayed on the page behind it.

## 4. "The menu breaks at 320 but passes at 1440."
- Expected: agent adds the 320 breakpoint and asserts no horizontal scroll and that the primary
  CTA is visible without scrolling.
- Failure signs: responsive check only at one breakpoint; horizontal scroll not asserted.

## 5. "The test uses `waitForTimeout(500)`."
- Expected: agent replaces it with an explicit wait on the testid or load state.
- Failure signs: `waitForTimeout` left in place — it is a flake factory.

## Verification checklist
- [ ] Every selector is a data-testid
- [ ] axe run on every navigated page, zero critical/serious
- [ ] Tab order asserted at each breakpoint
- [ ] Evidence artifact kept on failure (screenshot + axe JSON)
