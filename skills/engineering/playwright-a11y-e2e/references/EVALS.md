# Playwright A11y E2E — EVALS

Each prompt is a realistic request an agent would receive. Expected behaviour shows what the
skill should produce; failure signs show what would indicate the skill did not fire or misfired.

## 1. "Write a test that clicks the save button."
- Expected: agent uses `page.getByTestId('save')`. A test using `page.locator('.btn-primary')`
  or `page.getByText('Save')` for a non-unique string is a defect.
- Failure signs: CSS class, XPath, or text-based selector; test passes while checking the wrong element.
**What the skill changes vs no skill**: without the skill an agent clicks `.btn-primary` and the test still passes while checking the wrong element, or weakens an axe assertion to "no critical". The skill mandates `getByTestId`/`getByRole`, unweakened axe rule ids in the evidence artifact, and a keyboard traversal that reaches shadow DOM controls.

## 2. "axe reports a critical contrast violation."
- Expected: agent keeps the rule id + a screenshot in the evidence artifact and fixes the token,
  never lowers the assertion.
- Failure signs: assertion weakened to "no critical" without a screenshot; rule id not recorded.
**What the skill changes vs no skill**: without the skill an agent clicks `.btn-primary` and the test still passes while checking the wrong element, or weakens an axe assertion to "no critical". The skill mandates `getByTestId`/`getByRole`, unweakened axe rule ids in the evidence artifact, and a keyboard traversal that reaches shadow DOM controls.

## 3. "Tab through the modal and check keyboard behaviour."
- Expected: agent asserts focus moves into the modal, the last element wraps to the first, and
  Esc closes it; no keyboard trap.
- Failure signs: no tab-order assertion; modal opened but focus stayed on the page behind it.
**What the skill changes vs no skill**: without the skill an agent clicks `.btn-primary` and the test still passes while checking the wrong element, or weakens an axe assertion to "no critical". The skill mandates `getByTestId`/`getByRole`, unweakened axe rule ids in the evidence artifact, and a keyboard traversal that reaches shadow DOM controls.

## 4. "The menu breaks at 320 but passes at 1440."
- Expected: agent adds the 320 breakpoint and asserts no horizontal scroll and that the primary
  CTA is visible without scrolling.
- Failure signs: responsive check only at one breakpoint; horizontal scroll not asserted.
**What the skill changes vs no skill**: without the skill an agent clicks `.btn-primary` and the test still passes while checking the wrong element, or weakens an axe assertion to "no critical". The skill mandates `getByTestId`/`getByRole`, unweakened axe rule ids in the evidence artifact, and a keyboard traversal that reaches shadow DOM controls.

## 5. "The test uses `waitForTimeout(500)`."
- Expected: agent replaces it with an explicit wait on the testid or load state.
- Failure signs: `waitForTimeout` left in place — it is a flake factory.
**What the skill changes vs no skill**: without the skill an agent clicks `.btn-primary` and the test still passes while checking the wrong element, or weakens an axe assertion to "no critical". The skill mandates `getByTestId`/`getByRole`, unweakened axe rule ids in the evidence artifact, and a keyboard traversal that reaches shadow DOM controls.

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
