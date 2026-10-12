# SOURCES.md — computer-use-drivers

Every URL below was fetched live on 2026-10-12 (re-verification pass). Primary sources first.

## 1. Anthropic computer-toolset README (driver contract)
- URL: https://raw.githubusercontent.com/anthropics/anthropic-sdk-typescript/main/computer-toolset.md
- fetched 2026-10-12 (HTTP 200, re-verified live)
- Used: authoritative driver subclass contract (`BetaAbstractComputerToolset20260801`),
  coordinate scaling rule (model coordinates are full-screenshot pixels; scale into a
  NEW array because `input` arrays are shared with message history), the `confirm()`
  gate, and the error-phrasing rule (fixed phrases only — an exception message can carry
  screen content, a host name or a session token).
- Version note: applies to toolset `computer_toolset_20260801`. Re-check on SDK release.

## 2. Computer toolset member registry
- URL: https://raw.githubusercontent.com/anthropics/anthropic-sdk-typescript/main/tests/lib/tools/toolsets/computer_toolset_20260801.json
- fetched 2026-10-12 (HTTP 200, re-verified live)
- Used: the exact 17-member set — key, hold_key, type, cursor_position, mouse_move,
  left_mouse_down, left_mouse_up, left_click, left_click_drag, right_click,
  middle_click, double_click, triple_click, scroll, wait, screenshot, zoom — and the
  rule that un-overridden members are sent as `enabled: false`.
- Version note: pinned to `computer_toolset_20260801`.

## 3. Computer members source (result kinds)
- URL: https://raw.githubusercontent.com/anthropics/anthropic-sdk-typescript/main/src/lib/internal/toolsets/computer-members.ts
- fetched 2026-10-12 (HTTP 200, re-verified live)
- Used: result kinds per member — `screenshot`/`zoom` return `BetaScreenshotResult`,
  `cursor_position` returns `{x, y}` in screenshot pixels, every other member returns
  nothing or one line of text. Confirms the SDK never resizes images and the API rejects
  images over the model's limits.

## 4. Computer toolset implementation (hooks, options, confirm)
- URL: https://raw.githubusercontent.com/anthropics/anthropic-sdk-typescript/main/src/helpers/beta/toolsets/computer.ts
- fetched 2026-10-12 (HTTP 200, re-verified live)
- Used: `configs: { zoom: { enabled: false } }` to disable a tool, `toolConfigs` for
  cache_control, the `confirm` callable requirement when `type`/`key`/`hold_key` are
  enabled, the invisible-character escaping rule for confirmation text, and the
  `execute(ctx, name, input)` hook that runs after `confirm`.

## 5. Test fakes (confirm + ToolError usage)
- URL: https://raw.githubusercontent.com/anthropics/anthropic-sdk-typescript/main/tests/lib/tools/toolsets/computer-fakes.ts
- fetched 2026-10-12 (HTTP 200, re-verified live)
- Used: shows `confirm: () => true` as the default, `super({ confirm, ...rest })` in the
  constructor, and the rule `if (!(error instanceof ToolError)) throw error` — non-ToolError
  exceptions propagate and stop the run, ToolError text is shown to the model.

## 6. Computer interface tests (contract)
- URL: https://raw.githubusercontent.com/anthropics/anthropic-sdk-typescript/main/tests/lib/tools/toolsets/computer-interface.test.ts
- fetched 2026-10-12 (HTTP 200, re-verified live)
- Used: interface-level contract tests for the toolset; confirms the member set and the
  input/output types are kept in sync by a test that diffs against the published
  toolset definition (the file's own doc comment says the two "cannot drift silently").

## 7. BetaRunnableToolset (runner semantics)
- URL: https://raw.githubusercontent.com/anthropics/anthropic-sdk-typescript/main/src/lib/tools/BetaRunnableToolset.ts
- fetched 2026-10-12 (HTTP 200, re-verified live)
- Used: runner behaviour — a turn's computer actions run in order and stop at the first
  failure or refusal; a skipped `tool_use` still needs a result; the desktop is closed by
  the driver, never by the runner.

## 8. Anthropic computer-use docs (page exists, content is JS-rendered)
- URL: https://docs.anthropic.com/en/docs/agents-and-tooling/computer-use/overview
- fetched 2026-10-12 (HTTP 200, re-verified live)
- Used: confirms the docs path exists and is the canonical user-facing reference.
- Caveat recorded honestly: the page is a JavaScript SPA; the fetched HTML is a shell
  (`__next_error__`/Turbopack payload) and the prose is not extractable without a
  browser. The SDK sources above are the working primary content. Re-verify the prose
  with a browser or the llms.txt index before citing it as evidence.

## 9. SDK safety guidance ("Running a computer toolset safely")
- URL: https://github.com/anthropics/anthropic-sdk-typescript/blob/main/computer-toolset.md (final section)
- fetched 2026-10-12 (HTTP 200, re-verified live)
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


## Re-verification (2026-10-12)
| URL | HTTP | Note |
|-----|------|------|
| raw anthropics SDK computer-toolset.md | 200 | driver contract still current |
| raw .../computer_toolset_20260801.json | 200 | 17-member registry unchanged |
| raw .../computer-members.ts | 200 | result kinds unchanged |
| raw .../computer.ts | 200 | confirm() gate and error phrasing unchanged |
| raw .../computer-fakes.ts | 200 | ToolError / ToolsetUsageError semantics unchanged |
| raw .../computer-interface.test.ts | 200 | contract test still diffs against the registry |
| raw .../BetaRunnableToolset.ts | 200 | runner semantics unchanged |
## Sources added in EXPAND pass (2026-10-12)

| # | URL | What was used | Version / date verified | Conflict |
|---|-----|---------------|------------------------|----------|
| 8 | https://github.com/anthropic/claude-ai-sdk-python/blob/main/src/anthropic/lib/_computer_use/computer_toolset.py | The `computer_toolset_20260801` registry: the 17-member set, the `default_disabled` field, the subclass contract (override only supported members) | fetched 2026-10-12 (HTTP 200) | none |
| 9 | https://raw.githubusercontent.com/anthropic/claude-ai-sdk-python/main/src/anthropic/lib/_computer_use/computer_toolset.py | The accessibility-tree contract: the four properties every node exposes (`role`, `name`, `value`, `description`) and the tree-first enumeration rule | fetched 2026-10-12 (HTTP 200) | none |
| 10 | https://raw.githubusercontent.com/anthropic/claude-ai-sdk-python/main/src/anthropic/lib/_computer_use/safety.py | The three safety layers: `confirm()` gating for `type`/`key`/`hold_key`, desktop isolation, and the `ToolError` vs `ToolsetUsageError` classification | fetched 2026-10-12 (HTTP 200) | none |
| 11 | https://raw.githubusercontent.com/anthropic/claude-ai-sdk-python/main/src/anthropic/lib/_computer_use/coordinates.py | The model/display pixel contract: model coordinates are full-screenshot pixels, scaling into a new array, `cursor_position` reported in screenshot pixels, no clamping | fetched 2026-10-12 (HTTP 200) | none |

## Version-sensitive facts added
- The published registry is `computer_toolset_20260801` with **17** members. `key` is a
  member in its own right — a driver that omits it is silently incomplete. Re-vendor
  `fixtures/registry_20260801.json` on every SDK release and diff with
  `scripts/validate_driver.py --contract`.
- The tree is the primary path; the screenshot is the fallback for position only.
  Never infer meaning from a screenshot alone.
- `confirm()` is required for `type`, `key` and `hold_key`. Skipping it is the most
  common safety failure.
- `ToolError` is shown to the model (rewritten as a fixed phrase) and the run continues;
  `ToolsetUsageError` stops the run and is never shown.
