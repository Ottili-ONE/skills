# Safety layers — the three gates

Verified 2026-10-12 against the Anthropic SDK computer-toolset safety docs
(HTTP 200). A computer-use driver has three independent safety layers. Each one
alone is insufficient; they are designed to fail closed.

## Layer 1 — the confirm() gate

`confirm()` is **required** whenever `type`, `key` or `hold_key` is enabled. It is
not optional for the ungated members — it is simply not invoked.

The gate asks a human approver: "approve this tool call?". The approver sees the
**tool name and its input**, with every invisible character escaped. The model may
be relaying screen content, so what the approver reads must be exactly what runs.

### The fixed-phrase rule
- Confirmation text is a fixed phrase: `"type into the password field"`,
  `"press Enter in the terminal"`.
- It must **never** contain screen content, a host name, a session token, or a path
  that could be a secret. If the exception path needs to carry content, use the
  exception message — not the confirmation string.
- Escape invisible characters (zero-width spaces, homoglyphs, control codes) before
  showing the input. A homoglyph attack turns `rm -rf foo` into a string that looks
  identical to the approver but executes differently.

## Layer 2 — desktop isolation

The desktop runs in **one container or VM per session**:
- No credentials on the desktop. No host mounts. Egress only to the hosts the task needs.
- The model loop, the toolset and the API key stay **outside** the desktop.
- Treat the screen as untrusted: never execute, store as trusted, or forward screen
  contents, window titles or clipboard text unchecked.

A driver that runs on the host machine with credentials is not isolated, and a
single compromised screen image is a full host compromise.

## Layer 3 — error classification

| Exception type | Meaning | Action | Shown to the model? |
|----------------|---------|--------|---------------------|
| `ToolError` | backend failure that may carry screen content | rewrite as a fixed phrase; the run **continues** | yes, rewritten only |
| `ToolsetUsageError` | misuse: bad coordinates, disabled member, missing `confirm` | **stop the run** | no |
| any other exception | unexpected | stop the run; do not swallow | no |

The distinction matters because `ToolError` is shown to the model and the run
continues, while `ToolsetUsageError` stops it. Passing a raw exception message
through to the model is the P3 pitfall — that message can carry screen content.

## Ordered procedure for an error
1. Catch the exception; classify it.
2. If `ToolsetUsageError`, stop. Never retry the same input — the input is wrong, not
   the timing.
3. If `ToolError`, rewrite the message as a fixed phrase. Never pass `error.message`
   through.
4. If a coordinate is outside the display, throw `ToolError`. **Never clamp** —
   clamping silently clicks the wrong place and the model cannot detect it.
5. If an image exceeds the model's pixel limit, reject with `ToolError`. The SDK never
   resizes; reconfigure the capture resolution instead.

## Near-miss triggers
- Raw `error.message` in a tool result -> screen content leaks to the model.
- Clamping an out-of-bounds coordinate -> the model retries and compounds the mistake.
- Swallowing a non-`ToolError` exception -> the run continues with undefined state.
- `confirm()` absent from `type`/`key`/`hold_key` -> the action is ungated and destructive.
- Running the desktop on a host machine with credentials -> no isolation.
