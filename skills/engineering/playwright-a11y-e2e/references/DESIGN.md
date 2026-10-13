# DESIGN — playwright-a11y-e2e

## Trigger description (draft)
Fires when: an agent writes or reviews a Playwright E2E test; when an axe/a11y assertion fails;
when choosing selectors; when checking keyboard-only navigation or responsive breakpoints; or
when a test is flaky because it depends on animation, overlay timing, or a generated id.
Does NOT fire for: unit tests, static snapshots, or non-browser automation.

## What it does better than existing public skills
Playwright docs and the axe-core docs explain the tools; they do not give the Ottili selector
contract (data-testid only, never CSS class, never XPath, never text), the accessibility evidence
contract (every axe violation must carry a rule id + a screenshot + the DOM snippet in the
evidence artifact), or the responsive checklist (320/768/1024/1440 breakpoints with scroll
assertions). This skill also records the real incident: a test that asserted on a CSS class
broke silently for three sprints when the designer renamed the class, because the test reported
PASS (element found) while the wrong element was checked.

## Procedure outline
1. Selectors: `page.getByTestId('...')` only. A test that uses `page.locator('.btn')` or
   `page.getByText(...)` for a non-unique string is a defect.
2. axe: run `@axe-core/playwright` on every page after navigation; assert zero critical and
   serious violations; record rule ids in the evidence artifact.
3. Keyboard: tab through the whole tab order; every interactive control must be reachable and
   activate with Enter/Space; no keyboard traps.
4. Responsive: assert layout at 320/768/1024/1440; assert no horizontal scroll; assert the
   primary CTA is visible without scrolling at each breakpoint.
5. Stable waits: `waitForLoadState('networkidle')` or an explicit `waitForTestId`, never
   `waitForTimeout`.
6. Evidence: every failing run keeps the screenshot, the HAR, and the axe JSON; a PASS with no
   evidence is a claim.

## Scripts planned
- `scripts/check_axe_evidence.py` — validates an axe report JSON: every violation has rule id,
   nodes, and a linked screenshot path.

## Five eval prompts
1. "Write a test that clicks the save button." → agent must use a data-testid; using `.btn-primary`
   or `getByText('Save')` is a failure sign.
2. "axe reports a critical contrast violation." → agent must keep the rule id + screenshot in
   the evidence and fix the token, not lower the assertion.
3. "Tab through the modal." → agent must assert the focus moves into the modal, the last element
   wraps to the first, and Esc closes it.
4. "The test passes at 1440 but the menu breaks at 320." → agent must add the 320 breakpoint
   and assert no horizontal scroll.
5. "The test uses `waitForTimeout(500)`." → agent must replace it with an explicit wait on the
   testid or load state; `waitForTimeout` is a flake factory.
