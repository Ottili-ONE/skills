# SOURCES.md — computer-use-drivers

All URLs retrieved 2026-10-11 unless marked otherwise. Primary sources first.

## 1. Anthropic computer-toolset README (driver contract)
- URL: https://raw.githubusercontent.com/anthropics/anthropic-sdk-typescript/main/computer-toolset.md
- Retrieved: 2026-10-11 (HTTP 200)
- Used: authoritative driver subclass contract (`BetaAbstractComputerToolset20260801`),
  coordinate scaling rule (model coordinates are full-screenshot pixels; scale into a
  NEW array because `input` arrays are shared with message history), the `confirm()`
  gate, and the error-phrasing rule (fixed phrases only — an exception message can carry
  screen content, a host name or a session token).
- Version note: applies to toolset `computer_toolset_20260801`. Re-check on SDK release.

## 2. Computer toolset member registry
- URL: https://raw.githubusercontent.com/anthropics/anthropic-sdk-typescript/main/tests/lib/tools/toolsets/computer_toolset_20260801.json
- Retrieved: 2026-10-11 (HTTP 200)
- Used: the exact 16-member set — key, hold_key, type, cursor_position, mouse_move,
  left_mouse_down, left_mouse_up, left_click, left_click_drag, right_click,
  middle_click, double_click, triple_click, scroll, wait, screenshot, zoom — and the
  rule that un-overridden members are sent as `enabled: false`.
- Version note: pinned to `computer_toolset_20260801`.

## 3. Computer members source (result kinds)
- URL: https://raw.githubusercontent.com/anthropics/anthropic-sdk-typescript/main/src/lib/internal/toolsets/computer-members.ts
- Retrieved: 2026-10-11 (HTTP 200)
- Used: result kinds per member — `screenshot`/`zoom` return `BetaScreenshotResult`,
  `cursor_position` returns `{x, y}` in screenshot pixels, every other member returns
  nothing or one line of text. Confirms the SDK never resizes images and the API rejects
  images over the model's limits.

## 4. Computer toolset implementation (hooks, options, confirm)
- URL: https://raw.githubusercontent.com/anthropics/anthropic-sdk-typescript/main/src/helpers/beta/toolsets/computer.ts
- Retrieved: 2026-10-11 (HTTP 200)
- Used: `configs: { zoom: { enabled: false } }` to disable a tool, `toolConfigs` for
  cache_control, the `confirm` callable requirement when `type`/`key`/`hold_key` are
  enabled, the invisible-character escaping rule for confirmation text, and the
  `execute(ctx, name, input)` hook that runs after `confirm`.

## 5. Test fakes (confirm + ToolError usage)
- URL: https://raw.githubusercontent.com/anthropics/anthropic-sdk-typescript/main/tests/lib/tools/toolsets/computer-fakes.ts
- Retrieved: 2026-10-11 (HTTP 200)
- Used: shows `confirm: () => true` as the default, `super({ confirm, ...rest })` in the
  constructor, and the rule `if (!(error instanceof ToolError)) throw error` — non-ToolError
  exceptions propagate and stop the run, ToolError text is shown to the model.

## 6. Computer interface tests (contract)
- URL: https://raw.githubusercontent.com/anthropics/anthropic-sdk-typescript/main/tests/lib/tools/toolsets/computer-interface.test.ts
- Retrieved: 2026-10-11 (HTTP 200)
- Used: interface-level contract tests for the toolset; confirms the member set and the
  input/output types are kept in sync by a test that diffs against the published
  toolset definition (the file's own doc comment says the two "cannot drift silently").

## 7. BetaRunnableToolset (runner semantics)
- URL: https://raw.githubusercontent.com/anthropics/anthropic-sdk-typescript/main/src/lib/tools/BetaRunnableToolset.ts
- Retrieved: 2026-10-11 (HTTP 200)
- Used: runner behaviour — a turn's computer actions run in order and stop at the first
  failure or refusal; a skipped `tool_use` still needs a result; the desktop is closed by
  the driver, never by the runner.

## 8. Anthropic computer-use docs (page exists, content is JS-rendered)
- URL: https://docs.anthropic.com/en/docs/agents-and-tooling/computer-use/overview
- Retrieved: 2026-10-11 (HTTP 200, 131 KB)
- Used: confirms the docs path exists and is the canonical user-facing reference.
- Caveat recorded honestly: the page is a JavaScript SPA; the fetched HTML is a shell
  (`__next_error__`/Turbopack payload) and the prose is not extractable without a
  browser. The SDK sources above are the working primary content. Re-verify the prose
  with a browser or the llms.txt index before citing it as evidence.

## 9. SDK safety guidance ("Running a computer toolset safely")
- URL: https://github.com/anthropics/anthropic-sdk-typescript/blob/main/computer-toolset.md (final section)
- Retrieved: 2026-10-11
- Used: the three safety rules this skill's procedure is built on — isolate the desktop
  (one container/VM per session, no credentials, no host mounts, egress only to hosts
  the task needs), gate consequential actions with `confirm`, and treat the screen as
  untrusted (never execute, store as trusted or forward screen contents, window titles
  or clipboard text unchecked).

## Conflicts between sources
- No conflicts on the member set or the coordinate rule. The docs page (source 8) could
  not be read as prose; this is recorded as a retrieval limitation, not a contradiction.
  The SDK sources are authoritative for the contract.

## Version-sensitive facts and re-verification

| Fact | Verified for | Re-verify |
|------|-------------|-----------|
| Toolset type | computer_toolset_20260801 | on every SDK release |
| Member set (16) | 2026-08-01 toolset | on every SDK release |
| Coordinate semantics | screenshot pixels | on every SDK release |
| confirm() requirement | type/key/hold_key enabled | on every SDK release |
| ToolError vs ToolsetUsageError | current SDK | on every SDK release |
