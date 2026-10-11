# DESIGN: mcp-2026-07-28

## Trigger description (SKILL.md description draft, <=1024 chars)
"Build and consume stateless MCP servers and clients on the 2026-07-28 revision:
server/discover, per-request metadata via _meta, tasks extension, OAuth 2.1 with PKCE,
backward-compat negotiation down to 2025-11-25 and 2026-07-28. Use when an agent must
scaffold an MCP server or client, debug a protocol handshake, map error codes to actions,
or verify that a deployment is stateless and version-pinned. Not for general API design."

## Procedure outline
1. Pin the revision in config (never in logic): primary 2026-07-28, fallbacks 2025-11-25, 2025-06-18.
2. Server: implement server/discover (MUST), advertise capabilities in _meta, no initialize handshake.
3. Client: send protocolVersion + clientCapabilities + clientInfo in every request _meta; negotiate down.
4. Streamable HTTP: no Mcp-Session-Id, no protocol-level sessions; send MCP-Protocol-Version header.
5. Tasks extension: use resultType + InputRequiredResult for long-running tools; poll with tasks/get.
6. OAuth 2.1: Authorization Code with PKCE; Client ID Metadata Documents replace Dynamic Client Registration.
7. Error codes: JSON-RPC 2.0 range plus -32020..-32099 reserved for MCP; map each to an action.
8. Verify statelessness: replay a request with the same _meta and assert identical result; assert no session state.

## Scripts planned
- `scripts/protocol_check.py` — validates a server's discover response against schema.ts rules.
- `scripts/version_negotiate.py` — given client+server version lists, returns the agreed version or FAIL.
- `scripts/stateless_probe.py` — replays a request and asserts idempotent statelessness.

## Five eval prompts
1. "My MCP server still sends Mcp-Session-Id. Is it 2026-07-28 compliant?" -> FAIL: sessions removed.
2. "Client talks 2025-06-18, server only 2026-07-28. What happens?" -> negotiate down or connection refused; never silently downgrade security.
3. "Where does per-request metadata go?" -> in the `_meta` reserved-key block on every request.
4. "A tool runs for 3 minutes. How do I call it?" -> tasks extension with resultType and InputRequiredResult.
5. "List the OAuth flow for a new client." -> Authorization Code + PKCE, Client ID Metadata Document; DCR is deprecated.

## What this skill does better than a generic agent
A generic agent knows "MCP is a protocol"; this skill pins the exact revision, gives the
MUST/MAY/removed rule table, the error-code action map, and a stateless-replay probe. It
prevents the common incident of shipping a 2025-06-18 server that breaks on a 2026-07-28
client because the initialize handshake was removed.
