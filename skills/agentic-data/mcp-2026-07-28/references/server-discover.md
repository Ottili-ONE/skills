# server/discover — the 2026-07-28 MUST procedure

Verified 2026-10-12 against the 2026-07-28 changelog (HTTP 200) and SEP-2575
(raw HTTP 200). `server/discover` is a **MUST** on every 2026-07-28 server; it
replaces the removed `initialize` handshake as the version-capabilities exchange.

## When to call it
- Before the first tool call, to learn `supportedVersions` and `capabilities`.
- After any `-32022` (UnsupportedProtocolVersion), to re-read the server's list.
- On reconnect, because a server's advertised versions can change between releases.

## Request
```
POST /mcp HTTP/1.1
Host: example.com
MCP-Protocol-Version: 2026-07-28
MCP-Method: server/discover
Content-Type: application/json

{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "server/discover",
  "params": {},
  "_meta": {
    "io.modelcontextprotocol/protocolVersion": "2026-07-28",
    "io.modelcontextprotocol/clientInfo": { "name": "my-client", "version": "1.4.0" },
    "io.modelcontextprotocol/clientCapabilities": { "extensions": { "io.modelcontextprotocol/tasks": {} } }
  }
}
```
`params` is an empty object. There is no `initialize` and no session cookie.

## Response shape (MUST fields)
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "supportedVersions": ["2026-07-28", "2025-11-25"],
    "capabilities": {
      "tools": { "listChanged": false },
      "resources": { "subscribe": false },
      "logging": {},
      "extensions": { "io.modelcontextprotocol/tasks": { "methods": ["tasks/get", "tasks/update", "tasks/cancel"] } }
    },
    "serverInfo": { "name": "example-server", "version": "2.1.0" }
  }
}
```

| Field | Type | MUST | Notes |
|-------|------|------|-------|
| `supportedVersions` | array of strings | yes | non-empty, no duplicates, every entry in the vendored allowed list |
| `capabilities` | object | yes | may be empty `{}`; do not advertise `tasks/result` or `tasks/list` (removed) |
| `serverInfo` | object | yes | MUST contain `name` and `version`; extra keys are INFO only |

## What `server/discover` is NOT
- Not a negotiation step. It *informs* negotiation; the client still picks the
  highest common version and refuses with `-32022` on an empty intersection.
- Not a health check. A discover failure returns `-32601` with HTTP 404 — it means
  the method is absent, which means the server is not 2026-07-28.
- Not a substitute for per-request `_meta`. Discover runs once; every subsequent
  request still carries its own `_meta`.

## Ordered procedure
1. Call `server/discover` with `_meta` containing `protocolVersion`.
2. Read `supportedVersions`; intersect with the client's list (vendored allowed
   list only).
3. If the intersection is empty, refuse with `-32022` — never guess a version.
4. Agree on the **highest** common version; store it in config, never in logic.
5. Read `capabilities.extensions` to know whether the tasks extension is available.
   It is only usable if the client also declares it in per-request
   `clientCapabilities.extensions`.

## Near-miss triggers
- `server/discover` returns `-32601` -> the server does not implement it -> not
  2026-07-28; upgrade or pin the client to the server's version in config.
- `supportedVersions` contains a revision not in the vendored allowed list -> WARN;
  the server is ahead of or outside this skill's known set.
- `capabilities.tasks` advertises `tasks/result` or `tasks/list` -> FAIL; those were
  removed in 2026-07-28 (checked by `scripts/protocol_check.py`).
- Skipping discover and hardcoding `"2026-07-28"` -> the next revision breaks you.
