# Platform quirks — computer-use-drivers

Verified 2026-10-13 against the anthropic-sdk-python sources
(`lib/tools/_toolsets/_computer_registry.py`, `lib/tools/_toolsets/_computer.py`;
HTTP 200). The Python SDK is the primary source for this skill — the typescript
sources moved under `tests/` and the old `lib/_computer_use/` paths 404. These are
the differences between the driver contract and what actually works.

## Coordinate scaling

Model coordinates are **full-screenshot pixels**. The driver scales them into
the host's coordinate space. Rule: **scale into a NEW array** — the `input`
arrays are shared with message history, so mutating them in place corrupts the
conversation. Verified in `lib/tools/_toolsets/_computer.py`: the
`cursor_position` docstring (line 146) states it returns the cursor in screenshot
pixels, and the scaling rule is a driver obligation — the SDK never checks `input`.

## The 17-member set

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
`confirm=None`, which raises `ToolsetConfigError` at construction — so a driver
that serves any of the three keyboard members cannot be built without a
confirmation function. Confirmation text must have every invisible character
**escaped** (zero-width spaces, homoglyphs, control codes) so the approver reads
exactly what runs — the danger is that invisible characters are *not visible* to
the approver, so a homoglyph attack can turn `rm -rf foo` into a string that
looks identical but executes differently. Use a fixed phrase only; never put
screen content, a host name or a session token in the confirmation string. The
`execute(ctx, name, input)` hook runs *after* `confirm`.

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

## Near-miss triggers (platform-specific — the cross-cutting list lives in SKILL.md)

- macOS: a denied Accessibility grant is a hard stop, not a fallback — request at
  launch and fail closed.
- macOS: `screenshot` and `zoom` return `BetaScreenshotResult`; on Windows these
  come back as raw bytes, so a backend-agnostic driver must branch on platform.
- Linux: AT-SPI2 is shallow and flaky on Wayland — use X11 sessions when the tree
  comes back empty; do not fall back to pixels for *meaning*.
- Windows: UIA enumeration is the slowest of the three; do not re-enumerate the
  tree on every click — cache it per turn and refresh only on focus change.
- All platforms: `cursor_position` returns `{x, y}` in **screenshot** pixels,
  never host pixels; reporting host pixels makes every subsequent click land
  off-target and the model cannot detect it.
