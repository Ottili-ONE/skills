# Per-request `_meta` schema — 2026-07-28

Verified 2026-10-12 against SEP-2575 (raw HTTP 200). Every JSON-RPC request in
this revision carries a `_meta` block. There is no `initialize` handshake, so
`_meta` is the *only* place protocol state travels.

## The four reserved keys

| Key | Type | MUST | Content |
|-----|------|------|---------|
| `io.modelcontextprotocol/protocolVersion` | string | yes on every request | the client's negotiated revision, e.g. `"2026-07-28"` |
| `io.modelcontextprotocol/clientInfo` | object | yes on every request | `{ "name": <string>, "version": <string> }` |
| `io.modelcontextprotocol/clientCapabilities` | object | yes on every request | the capabilities the client supports; see below |
| `io.modelcontextprotocol/logLevel` | string | no | `"debug" \| "info" \| "notice" \| "warning" \| "error"` |

All keys live in the `io.modelcontextprotocol/*` namespace. A request that
omits `protocolVersion`, `clientInfo` or `clientCapabilities` is malformed; the
server returns `-32021` (MissingRequiredClientCapability) with HTTP 403.

## `clientCapabilities` shape
```json
"clientCapabilities": {
  "extensions": {
    "io.modelcontextprotocol/tasks": {}
  },
  "roots": { "listChanged": false },
  "sampling": {},
  "elicitation": {}
}
```
- `extensions` is a map of extension identifier -> empty object. The tasks
  extension is only usable if it appears here **and** the server advertised it in
  `server/discover.capabilities.extensions`.
- `roots`, `sampling`, `elicitation` are deprecated features. Declare them only
  if you consume them; servers MUST NOT infer capabilities from prior requests.

## Servers MUST NOT infer
A server that remembers "client X sent tasks last time" and serves `tasks/get`
without the client declaring the extension on this request is non-conformant.
Per-request `clientCapabilities` is the contract. This is the P3 pitfall.

## Ordered procedure
1. Negotiate the revision via `server/discover` (see `references/server-discover.md`).
2. Build `_meta` with all four keys (omit `logLevel` unless logging is needed).
3. Send `_meta` on **every** request — tools, resources, prompts, the tasks
   extension methods, everything.
4. On `-32021`, add the missing capability to `clientCapabilities` and resend;
   do not retry the identical request.

## Near-miss triggers
- Sending `_meta` only on the first request -> the server returns `-32021` on the
  second. Per-request means per-request.
- Putting `protocolVersion` in `params` instead of `_meta` -> ignored.
- Assuming the server infers capabilities -> non-conformant behaviour, and fragile.
- Omitting `clientInfo` -> `-32021` on a strict server.
