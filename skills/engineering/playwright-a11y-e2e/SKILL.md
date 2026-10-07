---
name: playwright-a11y-e2e
description: "End-to-end browser tests with Playwright and axe-core: axe accessibility scans, keyboard-only navigation checks, responsive breakpoint checks, and stable-selector rules."
license: MIT-compat
compatibility: "framework-agnostic; Node.js host; Linux; Playwright browsers installed"
metadata: {}
allowed-tools: []
---
# Playwright A11y E2E Skill (body <500 lines) Full procedure in references/playwright-a11y-e2e-procedure.md When to use - automated E2E coverage needed - accessibility conformance evidence required - responsive breakpoint checks needed - choosing selectors that survive refactors When NOT - unit or API tests - static HTML/CSS inspection - sites that cannot be automated CAPTCHA auth wall Decision table Goal | Tool | Evidence Accessibility | axe-core via Playwright | axe JSON Keyboard | Playwright keyboard API | video+log Responsive | viewport loop | screenshot set Selectors | getByRole/getByLabel | selector audit Procedure summary refs/procedure Numbered steps follow there Pitfalls - axe on dynamic modals misses aria-hidden flips wait aria-hidden=false - :focus-visible not WCAG criterion do not assert - nth-child breaks every refactor prefer getByRole - keyboard tests skip shadow DOM fail silently Web Components Checklist axe zero A/AA violations keyboard covers interactive responsive breakpoints pass selectors role-based evidence committed referenced EOF

## When to use this skill (trigger)
- You need automated E2E coverage of a web app.
- You need accessibility conformance evidence (axe scans, keyboard-only paths).
- You need responsive breakpoint checks.
- You are choosing selectors that survive refactors.

## When NOT to use this skill
- Unit or API tests (use pytest or contract tests).
- Static HTML/CSS inspection (use axe-core directly).
- Sites that cannot be automated (CAPTCHA, auth wall with no test credentials).

## Decision table — test strategy
| Goal | Primary tool | Evidence |
|------|--------------|----------|
| Accessibility conformance | axe-core via Playwright | axe JSON report |
| Keyboard-only navigation | Playwright keyboard API | video + log |
| Responsive breakpoints | Playwright viewport loop | screenshot set |
| Stable selectors | Playwright getByRole/getByLabel | selector audit |

## Numbered procedure (summary; full recipe in references/playwright-a11y-e2e-procedure.md)
1. Set up the browser context — install Playwright browsers, set a stable viewport, disable animations.
2. Run axe scans — @axe-core/playwright on each route; collect violations.
3. Verify keyboard-only paths — tab through every interactive element; assert focus order.
4. Check responsive breakpoints — loop over configured viewports; assert no overflow.
5. Use stable selectors — prefer role/label/text; never XPath or CSS classes.
6. Record evidence — axe JSON, screenshots, and a selector audit.

## Pitfalls from research
- axe on dynamic modals misses content rendered after aria-hidden flips; wait for aria-hidden=false.
- CSS :focus-visible is not a WCAG criterion; do not assert on it.
- nth-child selectors break on every refactor; prefer getByRole.
- Keyboard-only tests that skip shadow DOM fail silently on Web Components.
- Viewport loop must include 320px, 768px, 1024px, 1440px minimum (common trap: only testing desktop).
- axe run without frame handling misses content in iframes (common trap).

## Verification checklist (all must pass before you finish)
- [ ] axe scan runs on every route with zero violations of level A/AA [WCAG].
- [ ] Keyboard-only path covers every interactive element [WCAG].
- [ ] Responsive breakpoints pass at configured widths [responsive].
- [ ] Selectors are role/label-based, not XPath or CSS-class [stable selectors].
- [ ] Evidence files (axe JSON, screenshots) are committed or referenced [evidence].
