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
Expected: The **client** negotiates, not the server. The client sends its
`protocolVersion` in every request `_meta`; the server responds with the *highest*
version present in both lists (client ∩ server). Here the intersection is empty, so
the connection is refused with `-32022` UnsupportedProtocolVersion — never silently
downgrade, never fake a version the server does not advertise. The three live
versions are 2026-07-28, 2025-11-25, 2025-06-18; a client that only knows 2025-06-18
cannot reach a 2026-07-28-only server and must upgrade or fail closed.
Failure signs: assuming the server adapts automatically; hardcoding a version in
logic; treating a refusal as a retryable warning.

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

## E7 — the tasks/result trap
Prompt: "My long-running tool returns a `tasks/result` object. Is that right?"
Expected: No. `tasks/result` was removed in 2026-07-28; the tasks feature moved from
core into the `io.modelcontextprotocol/tasks` extension. Poll with `tasks/get`,
send client input with `tasks/update`, and cancel with `tasks/cancel`. The extension
is only available to clients that declare it in per-request
`clientCapabilities.extensions`.
Failure signs: calling `tasks/result`; assuming tasks is still a core method.

## E8 — the DCR trap
Prompt: "I use Dynamic Client Registration to onboard every new MCP client."
Expected: Stop. DCR is deprecated (PR #2858) and kept only for backwards
compatibility with authorization servers that do not support Client ID Metadata
Documents. For a new client, use the document flow; persist credentials keyed by
issuer and re-register when the issuer changes; validate `iss` before redeeming the
code (RFC 9207).
Failure signs: treating DCR as the current path; reusing credentials across issuers.

## E9 — the header-casing trap
Prompt: "My server rejects my POST because I sent `mcp-method` instead of `Mcp-Method`."
Expected: Treat the `Mcp-*` headers as case-insensitive per HTTP/1.1 and pin the
casing in config only after a primary re-fetch. The primary spec text uses
`Mcp-Method`, `Mcp-Name`, `MCP-Protocol-Version`; a server that is strict about
casing is non-conformant, but do not rely on that — normalise on your side.
Failure signs: hardcoding one casing in logic and blaming the other side.

## E10 — OAuth discovery-first vs DCR
Prompt: "Register a new MCP client with the authorization server. Do I use Dynamic
Client Registration?"
Expected: No for a new client. The 2026-07-28 revision deprecates Dynamic Client
Registration (RFC 7591, PR #2858) in favour of OAuth 2.1 Authorization Code + PKCE
(S256 only, `code_verifier` 43-128 chars) with a Client ID Metadata Document fetched
from `/.well-known/client-id-metadata`. DCR is kept only for backwards
compatibility with ASes that do not support the document flow. Credentials are keyed
by issuer; re-register when the issuer changes. Validate `iss` before redeeming the
code (RFC 9207, SEP-2468).
Failure signs: calling `/register` for a new client; storing one global
`client_id`; skipping `iss` validation; sending `client_secret` when the metadata
document declared `token_endpoint_auth_method: none`.

## E11 — poll a task correctly
Prompt: "A tool returns `resultType: "task"`. How do I get the result?"
Expected: Read `task.id` from the result, then poll `tasks/get` (from the
`io.modelcontextprotocol/tasks` extension) until the status is terminal
(`completed`, `failed`, `cancelled`, `suspended`). If the result carries
`resultType: "input_required"`, it is a Multi Round-Trip Request — respond with
`tasks/update` carrying `inputResponses`, do not abort. `tasks/result` and
`tasks/list` were removed in 2026-07-28 and return `-32601`.
Failure signs: calling `tasks/result`; blocking on the original tool call;
treating `input_required` as an error; polling without declaring the extension on
both sides.

## E12 — refuse a silent downgrade
Prompt: "My client and server both list 2026-07-28 and 2025-06-18. Which version do
we use?"
Expected: The **highest** common version, 2026-07-28. Negotiation picks
`max(client ∩ server ∩ ALLOWED)`; picking the lowest to "maximise compatibility"
weakens security and loses `server/discover`. If the intersection is empty the
connection is refused with `-32022`, never silently downgraded.
Failure signs: `min()` in negotiation code; a client that advertises only
2025-06-18 reaching a 2026-07-28-only server and expecting it to work.

## Near-miss prompts (trigger precision — these should NOT fire this skill)

## N1 — a non-MCP JSON-RPC service
Prompt: "I'm building a JSON-RPC 2.0 service that is not MCP. Do I need the 2026-07-28 revision?"
Expected: No. This skill is about the *Model Context Protocol* specifically — the `initialize`/`server/discover`/`_meta`/`tasks` machinery is MCP-shaped. A plain JSON-RPC service follows JSON-RPC 2.0, not MCP. Loading this skill would add MCP-specific fields to a protocol that has none.
Failure signs: adding `server/discover` or `_meta` to a non-MCP server; quoting MCP error codes for a JSON-RPC app.

## N2 — a synchronous tool that times out
Prompt: "My tool call returns an error after three minutes because the client timed out. How do I use the tasks extension?"
Expected: No. The tasks extension is for *structured* long-running work where the server returns `resultType: "task"` and the client polls `tasks/get`. A client-side timeout is a transport problem, not a tasks problem — there is no `resultType` in the error. Fix the timeout or use a longer one; do not bolt the tasks machinery onto a call that never declared it.
Failure signs: wrapping every tool call in tasks polling; treating a timeout as a tasks signal.

## N3 — client_credentials OAuth
Prompt: "I want to register a machine client using the OAuth 2.0 client_credentials grant."
Expected: No. MCP's OAuth story (2026-07-28) is Authorization Code with PKCE and Client ID Metadata Documents; `client_credentials` is a different grant from a different profile. This skill covers MCP's flow, not OAuth in general. Use an OAuth library or the AS's docs, not this skill.
Failure signs: citing MCP's `/authorize` and `/token` endpoints for a client_credentials flow; treating DCR as the replacement for client_credentials.
