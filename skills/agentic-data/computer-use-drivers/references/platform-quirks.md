# Platform quirks — computer-use-drivers

Verified 2026-10-11 against the anthropic-sdk-typescript sources
(`computer-toolset.md`, `computer-members.ts`, `computer.ts`, `computer-fakes.ts`,
`BetaRunnableToolset.ts`; all HTTP 200). These are the differences between the
driver contract and what actually works.

## Coordinate scaling

Model coordinates are **full-screenshot pixels**. The driver scales them into
the host's coordinate space. Rule: **scale into a NEW array** — the `input`
arrays are shared with message history, so mutating them in place corrupts the
conversation. Verified in `computer-toolset.md`.

## The 16-member set

Key, hold_key, type, cursor_position, mouse_move, left_mouse_down, left_mouse_up,
left_click, left_click_drag, right_click, middle_click, double_click, triple_click,
scroll, wait, screenshot, zoom. Un-overridden members are sent as
`enabled: false`. Pinned to `computer_toolset_20260801`.

## Result kinds

`screenshot`/`zoom` return `BetaScreenshotResult`; `cursor_position` returns
`{x, y}` in screenshot pixels; every other member returns nothing or one line of
text. The SDK never resizes images; the API rejects images over the model's
limits.

## The confirm gate

`type`, `key` and `hold_key` require a `confirm` callable. The default is
`confirm: () => true`. Confirmation text must use **invisible characters** so it
does not appear in the model's context as visible text. The `execute(ctx, name,
input)` hook runs *after* `confirm`.

## Error handling

`if (!(error instanceof ToolError)) throw error` — non-`ToolError` exceptions
propagate and stop the run; `ToolError` text is shown to the model. An exception
message must never carry screen content, a host name or a session token
(error-phrasing rule).

## Runner semantics

A turn's computer actions run in order and stop at the first failure or
refusal. A skipped `tool_use` still needs a result. The desktop is closed by the
**driver**, never by the runner.

## Sandbox rules

Isolate the desktop (one container/VM per session, no credentials, no host
mounts, egress only to hosts the task needs), gate consequential actions with
`confirm`, and treat the screen as untrusted (never execute, store as trusted or
forward screen contents, window titles or clipboard text unchecked).

## Near-miss triggers

- Scaling coordinates in place -> message history corrupted.
- Omitting `confirm` for `type`/`key`/`hold_key` -> the SDK throws.
- Catching all exceptions and showing their `.message` to the model -> screen
  content leaks.
- Letting the runner close the desktop -> double-close or leaked process.
- Treating `cursor_position` as returning host pixels -> it returns screenshot
  pixels.
