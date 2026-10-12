# Procedures — computer-use-drivers

Verified 2026-10-12 against the anthropic-sdk-typescript sources
(`computer-toolset.md`, `computer-members.ts`, `computer.ts`, `BetaRunnableToolset.ts`).
Step-by-step instructions that SKILL.md links to on demand.

## P1 — set up the driver

1. Pick the toolset type: `computer_toolset_20260801` (17 members).
2. Subclass `BetaAbstractComputerToolset20260801`. Override only the members your
   backend supports; un-overridden members are sent as `enabled: false` by the SDK.
3. Write each tool as a **method**, never an arrow-function field — arrow fields
   compile but are not detected as served.
4. Pass `confirm` through the constructor. The default is `confirm: () => true`;
   set it to a real approver before enabling `type`/`key`/`hold_key`.

## P2 — scale coordinates

1. Every model coordinate is in **full-screenshot pixels**.
2. Scale into a **NEW array** — the `input` arrays are shared with message history,
   so mutating them in place corrupts the conversation.
3. Report `cursor_position` back in screenshot pixels.
4. Keep the capture size fixed for the session; do not resize the screenshot mid-session.
5. Capture `zoom` regions at display resolution, not from the scaled screenshot.

## P3 — gate consequential actions

1. `type`, `key` and `hold_key` MUST run through `confirm()` before execution.
2. `confirm` sees the tool and its input, not what a click does on the screen.
3. If the desktop has apps that can send, pay or delete, approve clicks too.
4. With a terminal/run dialog focused, whatever is typed runs as a command — gate it.
5. Escape every invisible character in the confirmation text so the approver reads
   exactly what runs.

## P4 — phrase errors safely

1. Rewrite exceptions as fixed phrases. An exception's message can carry screen
   content, a host name or a session token, and the model reads tool error text
   unredacted.
2. `if (!(error instanceof ToolError)) throw error` — non-`ToolError` exceptions
   propagate and stop the run as a `ToolsetUsageError`; `ToolError` text is shown to
   the model and the run continues.
3. Never clamp out-of-bounds coordinates — throw `ToolError`. Clamping silently
   clicks the wrong place.

## P5 — isolate the desktop

1. One container or VM per session. No credentials, no host mounts.
2. Egress only to hosts the task needs.
3. Keep the model loop, the toolset and the API key outside the desktop.
4. Treat the screen as untrusted: never execute screen content; store as trusted only
   after explicit human review; forward window titles or clipboard text only after
   the same review.
5. The desktop is closed by the **driver**, never by the runner.

## P6 — background input

1. Run input non-blocking where the platform allows.
2. Poll the accessibility tree rather than assume the UI is static.
3. Never block the model loop on a UI modal.

## P7 — platform specifics

- **macOS**: AX API is the deepest tree but requires permissions; sandboxed apps may
  not expose their tree; use `screencapture` for images.
- **Windows**: UI Automation exposes more but is slower; coordinates are display
  pixels; apply high-DPI scaling consistently.
- **Linux**: AT-SPI2; X11 vs Wayland changes screenshot and input paths — prefer X11.

## Near-miss triggers

- Scaling coordinates in place -> message history corrupted.
- Omitting `confirm` for `type`/`key`/`hold_key` -> the SDK throws.
- Catching all exceptions and showing their `.message` to the model -> screen content leaks.
- Letting the runner close the desktop -> double-close or leaked process.
- Treating `cursor_position` as returning host pixels -> it returns screenshot pixels.
