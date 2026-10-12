# Locator catalog — browser-agent-playwright

Locators are the grounding layer: every finding in a browser run must cite the
locator string that produced it, so the finding is re-verifiable without
re-running the browser. This page is the ordered hierarchy and the per-type
gotchas.

## Order (strongest to weakest)

| Rank | Locator | When to use | Gotcha |
|------|---------|-------------|--------|
| 1 | `getByRole(role, { name })` | any semantic element | `name` is the accessible name, not the visible text |
| 2 | `getByLabel(label)` | form controls | matches the associated `<label>` |
| 3 | `getByTestId(id)` | app-authored hooks | requires `data-testid` in the markup |
| 4 | `getByText(text)` | last resort for static text | matches visible text only; case-insensitive substring |
| 5 | `locator('css selector')` | structural fallback | CSS does not see ARIA; use it for attributes only |
| 6 | `locator('xpath=...')` | absolute paths only | XPath is positional and breaks on any markup change |

Never use `page.evaluate` for extraction. It returns arbitrary JS and can be
hijacked (pitfall P1).

## Per-type gotchas

- **Buttons**: `getByRole('button', { name })`. The name comes from the
  accessible name computation — inner text, `aria-label`, or `title`. A button
  whose text is split across spans may need `name` with the full string.
- **Links**: `getByRole('link', { name })`. Same name rules.
- **Inputs**: `getByLabel` first; fall back to `getByRole('textbox', { name })`.
  Placeholder is not a label.
- **Tables**: `getByRole('row')` then `.evaluateAll`. Rows include the header;
  filter by `getByRole('columnheader')` if you need it separately.
- **iframes**: `page.frameLocator('iframe[src*="widget"]')` then `.getByRole(...)`
  **inside the frame**. Never use top-level `page` for inside-frame elements.
- **Dynamic content**: wait on the locator, not a timeout:
  `await expect(locator).toBeVisible()`.
- **Hidden elements**: `locator.textContent()` returns `null`. Wait for
  visibility first, then assert non-null.

## The grounding rule

Every extracted value is returned together with the locator string:

```js
return {
  headline,
  evidence: "page.getByRole('heading', { level: 1 }).first()"
};
```

A finding without an evidence locator is not a finding — it cannot be checked.
