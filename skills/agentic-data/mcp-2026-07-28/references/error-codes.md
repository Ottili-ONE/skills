# Error codes — mcp-2026-07-28

Verified 2026-10-12 against the 2026-07-28 changelog and SEP-2575.
JSON-RPC 2.0 reserved codes are unchanged; MCP renumbered its own range in this revision.

## Ranges

| Range | Meaning | Action |
|-------|---------|--------|
| `-32600` | JSON-RPC: Invalid Request | Reject the whole message; do not retry malformed JSON. |
| `-32601` | JSON-RPC: Method not found | The method name is wrong or unsupported. `server/discover` failures return this with HTTP 404. |
| `-32602` | JSON-RPC: Invalid params | Schema validation failed. Return the field path in `data`. |
| `-32603` | JSON-RPC: Internal error | Transport/JSON parse failure. Retry with backoff; do not treat as application logic. |
| `-32700` | JSON-RPC: Parse error | Not valid JSON. Retry; a persistent parse error means the framing is wrong. |
| `-32000..-32019` | Implementation-defined (grandfathered) | Legacy. Map to a named action in your own table; never invent meaning. |
| `-32020` | MCP: HeaderMismatch | A required `Mcp-*` header is missing or wrong. Fix the header, not the body. |
| `-32021` | MCP: MissingRequiredClientCapability | The client omitted a capability from per-request `clientCapabilities`. Add it; servers MUST NOT infer capabilities. |
| `-32022` | MCP: UnsupportedProtocolVersion | No version in the intersection of client and server lists. Refuse; never silently downgrade. |
| `-32023..-32099` | Reserved for MCP | Do not use. If you need a code, use `-32000..-32019` and document it. |

## Renumbering map (old -> new)

| Old code (2025-11-25) | New code (2026-07-28) | Meaning |
|-----------------------|----------------------|---------|
| `-32001` | `-32020` | HeaderMismatch |
| `-32003` | `-32021` | MissingRequiredClientCapability |
| `-32004` | `-32022` | UnsupportedProtocolVersion |

If you see an old code from a 2026-07-28 server, the server is not on this revision.

## HTTP status mapping

| Error | HTTP status |
|-------|-------------|
| `server/discover` not found | 404 |
| Missing `MCP-Protocol-Version` header | 400 |
| Unsupported version | 400 with `-32022` in the body |
| Missing required client capability | 403 with `-32021` |
| All other JSON-RPC errors | 200 with the error in the JSON-RPC body |

## Ordered response procedure

1. Read the `code` field.
2. If it is a JSON-RPC reserved code, fix the request framing or params.
3. If it is `-32020`, check the `Mcp-Method`/`Mcp-Name`/`MCP-Protocol-Version` headers (case-insensitive).
4. If it is `-32021`, add the missing capability to `clientCapabilities` on the next request.
5. If it is `-32022`, re-run `server/discover`, intersect the lists, and pin the agreed version in config.
6. If it is `-32000..-32019`, look up your own legacy map; if absent, treat as internal error.
7. Never retry a request that failed with `-32601` or `-32602` without changing something first.
