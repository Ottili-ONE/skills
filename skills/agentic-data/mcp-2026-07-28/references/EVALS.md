# EVALS — mcp-2026-07-28

Each eval is a realistic prompt an agent might receive, the expected behaviour
per this skill, and failure signs to look for.

## E1 — identify a 2026-07-28 server
Prompt: "My server sends `Mcp-Session-Id` and an `initialize` handshake. Is it
2026-07-28 compliant?"
Expected: No. The 2026-07-28 revision removed the `initialize` handshake, the
`Mcp-Session-Id` header and protocol-level sessions on Streamable HTTP. The server
must advertise capabilities via `server/discover` (MUST) and carry protocol fields in
every request's `_meta`.
Failure signs: "it still works, so it is compliant"; no `server/discover`.

## E2 — negotiate a version with an older client
Prompt: "My client speaks 2025-06-18 and the server only speaks 2026-07-28. What
happens?"
Expected: The client sends its `protocolVersion` in every request `_meta`; the server
negotiates down to a version it supports. If no overlap, the connection is refused —
never silently downgrade security-critical behaviour. The three live versions are
2026-07-28, 2025-11-25, 2025-06-18.
Failure signs: assuming the server adapts automatically; hardcoding a version in logic.

## E3 — locate per-request metadata
Prompt: "Where does the client send its protocol version and capabilities?"
Expected: In the reserved `_meta` block on every request, using the
`io.modelcontextprotocol/*` namespace keys `protocolVersion`,
`clientCapabilities` and `clientInfo`. No `initialize` handshake is needed.
Failure signs: putting them in request params; expecting a session to carry them.

## E4 — call a long-running tool
Prompt: "A tool runs for three minutes. How do I call it?"
Expected: Use the Tasks extension: the tool returns a result with `resultType` set, and
may return `InputRequiredResult` when it needs more input. Poll with `tasks/get`. The
extension keys live in the `io.modelcontextprotocol/tasks` namespace.
Failure signs: blocking on a plain tool call; not handling `InputRequiredResult`.

## E5 — map an OAuth flow for a new client
Prompt: "Register a new client for an MCP server under 2026-07-28."
Expected: Authorization Code flow with PKCE. Dynamic Client Registration is
deprecated (PR #2858); the replacement is Client ID Metadata Documents. No legacy
client-credentials shortcut.
Failure signs: using DCR as if it were still supported.

## E6 — verify statelessness
Prompt: "How do I prove my deployment is stateless?"
Expected: Replay a request with the same `_meta` and assert an identical result, and
assert no session state is stored between requests. On Streamable HTTP there is no
`Mcp-Session-Id` to manage.
Failure signs: "it works in practice" without a replay; relying on session IDs.
