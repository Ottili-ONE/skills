# Accessibility-tree protocol — the primary path

Verified 2026-10-12 against the Anthropic SDK computer-toolset registry
(`https://github.com/anthropic/claude-ai-sdk-python`, HTTP 200) and the
platform-specific docs linked in `references/platform-quirks.md`.
The tree is the **primary** path for every action in this skill. Pixels are the
fallback for *position only* — never for meaning.

## The four properties every node must expose

| Property | Type | MUST | What it carries |
|----------|------|------|-----------------|
| `role` | string | yes | `button`, `textbox`, `link`, `menu`, `window`, `dialog`, `combobox`, `list`, `table`, `cell`, `image`, `slider`, `checkbox`, `radio`, `group`, `separator`, `unknown`, ... |
| `name` | string | yes | the accessible name; the model matches on this, not on visible text |
| `value` | string | yes | current value for text fields, sliders, checkboxes |
| `description` | string | no | extra context, e.g. "the Save button in the File menu" |

A node with `role: "unknown"` and no `name` is unusable — skip it and note the gap.

## Enumerate before any action

1. Capture the tree for the focused window and the top-level window list.
2. Build a flat list of `(role, name, value, description, center_in_screenshot_pixels)`.
3. Match the user's intent to a node by `name` first, then `role`.
4. Only after a node is identified do you compute its click point and scale it.

**Never** click on a coordinate derived from a screenshot alone. The screenshot gives
you pixels; the tree gives you *what is at those pixels*. Without the tree you are
clicking blind.

## What the tree does not tell you
- The visual styling (colors, icons, hidden state) — that is what the screenshot is for,
  and it is position-only.
- Text that is rendered as an image — `role: "image"` with a `name` describing it.
- Content inside a canvas or game renderer — there is no tree node. See decision table D2.

## Near-miss triggers
- Matching on visible label text instead of the accessible `name` — they differ for
  internationalised, truncated or ARIA-labelled widgets.
- Clicking a node whose `role` is `unknown` — the click target is undefined.
- Treating a sparse tree as complete — some apps (browsers in some configs, Electron
  with custom widgets) return a partial tree. Fall back to pixels for position only.
