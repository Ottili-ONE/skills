# DESIGN: computer-use-drivers

## Trigger description (SKILL.md description draft, <=1024 chars)
"Drive a desktop application from an agent through a computer-use driver: accessibility
trees, screenshot-coordinate scaling, background input, confirmation gates and
platform quirks (Windows/macOS/Linux). Use when an agent must automate a desktop app
that a browser cannot reach; not for browser automation or remote-control via VNC
without a driver contract."

## Primary sources used
- Anthropic computer-toolset README (2026-08-01 toolset, 17 members):
  https://raw.githubusercontent.com/anthropics/anthropic-sdk-python/main/src/anthropic/lib/tools/_toolsets/_computer_registry.py
  (the typescript `computer-toolset.md` path no longer resolves; the Python SDK is
  the primary source for this skill, re-fetched 2026-10-13, HTTP 200)
  -> driver subclass contract, coordinate scaling, confirm() gate, error phrasing rules.
- Member registry:
  https://github.com/anthropics/anthropic-sdk-typescript/blob/main/tests/lib/tools/toolsets/computer_toolset_20260801.json
  -> exact member set: key, hold_key, type, cursor_position, mouse_move, left_mouse_down,
  left_mouse_up, left_click, left_click_drag, right_click, middle_click, double_click,
  triple_click, scroll, wait, screenshot, zoom.
- SDK safety guidance ("Running a computer toolset safely"): isolate the desktop, gate
  consequential actions, treat the screen as untrusted.

## Procedure outline
1. Isolate the desktop — one container/VM per session, no credentials, no host mounts,
   egress only to hosts the task needs. Keep the model loop, driver and API key outside.
2. Subclass the driver contract (e.g. `BetaAbstractComputerToolset20260801`); override only
   the members your backend supports. Un-overridden members are sent as `enabled: false`.
   Write tools as methods, never arrow-function fields (they compile but are not detected).
3. Scale coordinates: every model coordinate is in full-screenshot pixels. Scale into a
   NEW array — the arrays in `input` are shared with the message history. Report
   `cursor_position` back in screenshot pixels. Keep capture size fixed for the session.
   Capture `zoom` regions at display resolution, not from the scaled screenshot.
4. Gate consequential actions with `confirm()`. It sees the tool and its input, not what
   a click does on the screen. If the desktop has apps that can send, pay or delete,
   approve clicks too. With a terminal/run dialog focused, whatever is typed runs as a
   command. Escape every invisible character in the confirmation text.
5. Throw `ToolError` for missing/malformed fields, coordinates outside the display (do
   NOT clamp), and `duration`/`repeat`/`scroll_amount` your backend should not honor.
6. Phrase errors in fixed words: an exception message can carry screen content, a host
   name or a session token. A `ToolsetUsageError` propagates and stops the run.
7. Background input: run non-blocking where the platform allows; poll the accessibility
   tree rather than assume the UI is static; never block the model loop on a UI modal.

## Platform quirks
- Windows: accessibility tree via UI Automation; coordinates are host/display pixels;
  high-DPI scaling must be applied consistently.
- macOS: AX API; sandboxed apps may not expose their tree; `screencapture` for images.
- Linux: AT-SPI2; X11 vs Wayland changes screenshot and input paths.

## Five eval scenarios (expanded in `references/EVALS.md`)
1. "The model sent a coordinate outside the display. What do I do?" -> Throw ToolError;
   never clamp it.
2. "My confirm() function shows raw screen content. Is that a problem?" -> Yes: escape
   every invisible character; the approver must read what runs.
3. "I wrote a tool as an arrow-function field. What happens?" -> It compiles but is not
   detected as served; the API sends it as enabled: false.
4. "A tool threw an exception whose message contains the window title." -> That text is
   shown to the model unredacted; rewrite it as a fixed phrase.
5. "The desktop has a terminal focused and the model types 'rm -rf ...'." -> This is a
   consequential action; confirm() must approve it, and the desktop must be isolated.

## What this skill does better than a generic agent
A generic agent issues clicks and hopes. This skill pins the 2026-08-01 toolset
contract, the coordinate-scaling rule (with the shared-array trap), the confirmation
gate for consequential actions, the isolation requirement, and the error-phrasing rule
that prevents screen content leaking into tool errors. It prevents the common incident
of a driver that clamps out-of-bounds coordinates and then clicks the wrong place.

## What existing public skills do (and what this one does differently)

Surveyed on 2026-10-12; the SDK paths were re-verified 2026-10-13. `anthropics/skills` ships no computer-use skill — the
capability lives in the SDK (`computer_toolset_20260801`, 17 members), not in a
skill folder. The Fastio 2026 directory lists `Agent-Browser` (14k stars, ref-based
element targeting) and generic automation snippets; neither covers a desktop
accessibility-tree driver with a safety layer. `skills.cat` has no computer-use
entry.

This skill is the only one that turns the SDK contract into a *driver* procedure:
- **Tree-first, screenshot-fallback**: the accessibility tree (`role`, `name`,
  `value`, `description`) is the primary input; the screenshot supplies pixel
  coordinates for `mouse_move` only and is never interpreted as content.
- **Coordinate contract enforced**: model coordinates are full-screenshot pixels;
  scaling into a NEW array is required because `input` arrays are shared with
  message history. No clamping — out-of-range clicks are the driver's fault, not
  the model's.
- **Three safety layers**: `confirm()` gating for `type`/`key`/`hold_key`, desktop
  isolation (one container per session, no host mounts), and the
  `ToolError` vs `ToolsetUsageError` classification (a `ToolError` is rewritten to a
  fixed phrase and shown to the model; a `ToolsetUsageError` stops the run and is
  never shown).
- **17-member registry diffed against the SDK**: un-overridden members are sent as
  `enabled: false`; omitting `key` silently incompletes the driver.

Public sources surveyed (2026-10-12; the Python SDK paths re-fetched 2026-10-13, all HTTP 200):
| Source | What it has | Gap this skill fills |
|--------|-------------|---------------------|
| `anthropics/skills` | no computer-use skill at all | the SDK contract is not a skill; this one is |
| `Agent-Browser` (Fastio listing) | browser ref targeting | no desktop tree, no confirm() gate |
| Anthropic SDK `computer_toolset_20260801` | the raw contract | no procedure, no safety layers, no quirks table |
