# DESIGN: computer-use-drivers

## Trigger description (SKILL.md description draft, <=1024 chars)
"Drive a desktop application from an agent through a computer-use driver: accessibility
trees, screenshot-coordinate scaling, background input, confirmation gates and
platform quirks (Windows/macOS/Linux). Use when an agent must automate a desktop app
that a browser cannot reach; not for browser automation or remote-control via VNC
without a driver contract."

## Primary sources used
- Anthropic computer-toolset README (2026-08-01 toolset, 17 members):
  https://github.com/anthropics/anthropic-sdk-typescript/blob/main/computer-toolset.md
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
- Windows: accessibility tree via UI Automation; coordinates are display pixels;
  high-DPI scaling must be applied consistently.
- macOS: AX API; sandboxed apps may not expose their tree; `screencapture` for images.
- Linux: AT-SPI2; X11 vs Wayland changes screenshot and input paths.

## Five eval prompts (mirrored in `references/EVALS.md`)
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
