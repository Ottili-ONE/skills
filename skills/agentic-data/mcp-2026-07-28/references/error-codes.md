# Error codes — mcp-2026-07-28

Verified 2026-10-12 against
https://modelcontextprotocol.io/specification/2026-07-28/changelog (HTTP 200) and
SEP-2575 / SEP-2663 (raw, HTTP 200). The 2026-07-28 revision **renumbered** the
reserved code range. Old codes are grandfathered only.

## Ranges (current revision)

| Range | Meaning | Action |
|-------|---------|--------|
| `-32600` | Parse error | Fix the JSON; the request never reached the server |
| `-32601` | Method not found | The method is not in the server's capability set. `server/discover` failures also return this with HTTP 404 |
| `-32602` | Invalid params | Validate against the tool/inputSchema in `server/discover` |
| `-32603` | Internal error | Server bug or unexpected state; retry once, then log |
| `-32700` | Resource not found | The URI is wrong or was deleted |
| `-32000..-32019` | Implementation-defined (grandfathered) | Treat as opaque; map to a retry/no-retry decision by convention only |
| `-32020` | HeaderMismatch | A `Mcp-*` header is missing, malformed or conflicts with `_meta` |
| `-32021` | MissingRequiredClientCapability | The client omitted a capability the request needs |
| `-32022` | UnsupportedProtocolVersion | No version in common between client and server |

## Old-code mapping (2025-11-25 -> 2026-07-28)

| Old code | Old meaning | New code |
|----------|-------------|----------|
| `-32001` | HeaderMismatch | `-32020` |
| `-32003` | MissingRequiredClientCapability | `-32021` |
| `-32004` | UnsupportedProtocolVersion | `-32022` |

A client written against 2025-11-25 that still emits `-32004` will be refused by a
2026-07-28-only server that emits `-32022`. Detect by code, never by numeric range
alone: treat anything in `-32000..-32099` as "MCP-reserved" and branch on the exact
code.

## Ordered decision procedure on receipt of an error

1. **Read the code exactly.** Do not infer meaning from the range.
2. **`-32600` / `-32602`**: client-side fault. Re-serialize, re-validate params, retry.
3. **`-32601`**: confirm the method exists via `server/discover`; if it does, the
   capability is missing — ask the operator, do not guess.
4. **`-32022`**: re-run version negotiation. If the server list really has no
   overlap, stop and report the incompatibility. Never silently downgrade the client.
5. **`-32020` / `-32021`**: fix the header or the capability declaration, then retry.
6. **`-32603` / `-32700` / `-32000..-32019`**: retry once with exponential backoff
   (100 ms, 400 ms, cap 5 retries). If it persists, capture `_meta`, method and the
   full response and escalate.
7. **Never** retry a request that mutated state on a `-32601` or `-32022` without
   re-checking `server/discover` first.

## Near-miss triggers

- Matching on `-32004` when the server speaks only 2026-07-28 -> the server returns
  `-32022`, your matcher misses it, and you loop forever.
- Treating `-32000..-32019` as "unknown" and retrying blindly -> some implementors use
  them for permanent failures; retrying can duplicate a side effect.
- Reading the error from a wrapped HTTP body instead of the JSON-RPC error object ->
  the code field is nested under `error.code`.
