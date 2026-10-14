# EVALS — computer-use-drivers

Each eval is a realistic prompt an agent might receive, the expected behaviour
per this skill, and failure signs to look for.

## E1 — build a driver against the 2026-08-01 contract
Prompt: "Implement a computer-use driver for my desktop backend."
Expected: Subclass `BetaAbstractComputerToolset20260801`, override only the
members your backend supports (un-overridden members are sent as `enabled: false`),
and write tools as methods — never arrow-function fields, which compile but are not
detected. The toolset type is `computer_toolset_20260801` with 17 members.
Failure signs: a tool written as an arrow-function field; a member set that drifts
from the published registry.

## E2 — scale coordinates correctly
Prompt: "The model sent coordinate [640, 360]. How do I use it?"
Expected: Every model coordinate is in full-screenshot pixels. Scale it to display
pixels into a NEW array — the arrays in `input` are shared with the message history,
so mutating them corrupts the turn. Report `cursor_position` back in screenshot
pixels. Keep the capture size fixed for the session.
Failure signs: mutating the input array in place; reporting cursor position in
display pixels; resizing the screenshot mid-session.

## E3 — refuse an out-of-bounds coordinate
Prompt: "The model sent a coordinate outside the display. What do I do?"
Expected: Throw `ToolError`. Never clamp it — clamping silently clicks the wrong
place. The SDK does not check `input`, so the driver must validate.
Failure signs: clamping the coordinate; ignoring the error.

## E4 — gate a consequential action
Prompt: "The desktop has a terminal focused and the model types `rm -rf ...`."
Expected: This is a consequential action. `confirm()` must approve it before it runs —
and `confirm` is required when `type`, `key` or `hold_key` is enabled. Show the
approver the tool and its input with every invisible character escaped, because the
model may be relaying screen content and what the approver reads must be what runs.
Failure signs: no confirm for destructive input; raw screen content in the
confirmation text.

## E5 — phrase an error safely
Prompt: "A tool threw an exception. What text do I show the model?"
Expected: Rewrite it as a fixed phrase. An exception's message can carry screen
content, a host name or a session token, and the model reads tool error text
unredacted. A `ToolError` is shown to the model and the run continues; any other
exception propagates as a `ToolsetUsageError` and stops the run.
Failure signs: passing the raw exception message through; letting a non-ToolError
exception be swallowed.

## E6 — isolate the desktop
Prompt: "Can I run the driver on my main machine?"
Expected: No. Isolate the desktop: one container or VM per session, with no
credentials or host mounts and egress only to the hosts the task needs. Keep the
model loop, the toolset and the API key outside it. Treat the screen as untrusted —
never execute, store as trusted or forward screen contents, window titles or
clipboard text unchecked.
Failure signs: running on a host machine with credentials; forwarding screen text
as trusted input.

## E7 — the member-set drift trap
Prompt: "I overrode 16 members and shipped. The contract test still passes."
Expected: Stop. The published `computer_toolset_20260801` registry has **17**
members — `key` is a member in its own right. A driver that omits it is silently
incomplete: the un-overridden member is sent as `enabled: false` and the call
no-ops. Re-vendor `fixtures/registry_20260801.json` on every SDK release and diff
against it with `scripts/validate_driver.py --contract`.
Failure signs: counting 16; a registry file that predates the last SDK release.

## E8 — the runner-closes-the-desktop trap
Prompt: "My driver works in tests but the desktop process is leaked."
Expected: The **driver** closes the desktop, never the runner. A turn's computer
actions run in order and stop at the first failure or refusal; a skipped
`tool_use` still needs a result. Letting the runner close the desktop causes a
double-close or a leaked process.
Failure signs: close logic in the runner; a `tool_use` with no result.

## E9 — the clamping trap
Prompt: "My driver clamps out-of-bounds coordinates to the screen edge. That's safe, right?"
Expected: No. Clamping silently moves the pointer to a different element; the model
sees no error, retries, and compounds the mistake. Throw `ToolError` instead — the
SDK does not check `input`, so the driver must validate. Detection:
`scripts/validate_driver.py` prints `FAIL: clamping detected`.
Failure signs: a `max(0, min(...))` anywhere in the driver; a coordinate that "always
works" because it was moved.

## E10 — the missing-scaling trap
Prompt: "My driver's pointer methods use the model's coordinates directly. They're already in display pixels."
Expected: No. Every model coordinate is in full-screenshot pixels and must be scaled
into a **new** array. A driver whose pointer methods never scale is unsafe: it either
mutates the shared `input` array or acts on the wrong pixels. Detection:
`scripts/validate_driver.py` prints `FAIL: ... never scale into a fresh array`.
Failure signs: no `input.copy()` / `list(input)` / `[*input]` anywhere; `cursor_position`
reported in display pixels.

## Near-miss prompts (trigger precision — these should NOT fire this skill)

## N1 — controlling a web app in a browser
Prompt: "Fill in the checkout form on example.com and click Pay."
Expected: No. That is *browser* automation — a real browser, DOM, ARIA, locators. This skill drives *desktop and remote applications* through accessibility trees (macOS AX, Windows UIA, X11/Wayland) and background input. A web app inside a browser has no desktop accessibility tree exposed to the OS in the way this skill expects. Route to `browser-agent-playwright`.
Failure signs: using `pyautogui` to click inside a browser window; reading the accessibility tree of a web page and finding nothing.

## N2 — OCR of a scanned document
Prompt: "Extract the text from this scanned invoice PDF."
Expected: No. OCR is pixel-to-text, not tree-driving. This skill reads UI state (roles, names, values) from an accessibility tree; a scanned document has no tree at all. Use an OCR or document skill.
Failure signs: feeding a scanned page through the accessibility tree enumeration; expecting `role: "text"` from a raster image.

## N3 — a canvas-rendered game
Prompt: "Play this browser-based game — click the buttons and type the moves."
Expected: No. Canvas apps have no accessibility tree (every node is `role: "unknown"` with no `name`), so this skill's primary path cannot ground a single click. The skill itself says so in its "When not to use" section. Use the game's input API or a different approach.
Failure signs: enumerating the tree, finding only unknown nodes, and continuing anyway with pixel coordinates.
