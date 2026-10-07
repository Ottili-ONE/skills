---
name: playwright-a11y-e2e
description: "End-to-end browser tests with Playwright and axe-core: axe accessibility scans, keyboard-only navigation checks, responsive breakpoint checks, and stable-selector rules."
license: MIT-compat
compatibility: "framework-agnostic; Node.js host; Linux; Playwright browsers installed"
metadata: {}
allowed-tools: []
---
# Playwright A11y E2E Skill (body <500 lines) Full procedure in references/playwright-a11y-e2e-procedure.md When to use - automated E2E coverage needed - accessibility conformance evidence required - responsive breakpoint checks needed - choosing selectors that survive refactors When NOT - unit or API tests - static HTML/CSS inspection - sites that cannot be automated CAPTCHA auth wall Decision table Goal | Tool | Evidence Accessibility | axe-core via Playwright | axe JSON Keyboard | Playwright keyboard API | video+log Responsive | viewport loop | screenshot set Selectors | getByRole/getByLabel | selector audit Procedure summary refs/procedure Numbered steps follow there Pitfalls - axe on dynamic modals misses aria-hidden flips wait aria-hidden=false - :focus-visible not WCAG criterion do not assert - nth-child breaks every refactor prefer getByRole - keyboard tests skip shadow DOM fail silently Web Components Checklist axe zero A/AA violations keyboard covers interactive responsive breakpoints pass selectors role-based evidence committed referenced EOF
