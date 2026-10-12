# Compatibility matrix — mcp-2026-07-28

Verified 2026-10-12 against the 2026-07-28 changelog (HTTP 200) and SEP-2575.
This table answers "what breaks when I pair revision X with revision Y".

## Rows = server revision, columns = client revision

| Server \ Client | 2026-07-28 | 2025-11-25 | 2025-06-18 |
|-----------------|------------|------------|------------|
| 2026-07-28 | agree on 2026-07-28 | server downgrades to 2025-11-25 | server downgrades to 2025-06-18 |
| 2025-11-25 | client downgrades to 2025-11-25 | agree on 2025-11-25 | client downgrades to 2025-06-18 |
| 2025-06-18 | **refuse** (-32022) unless server is upgraded | **refuse** (-32022) | agree on 2025-06-18 |

Rule: agree on the **highest common version**. Never silently pick a lower one —
the client must explicitly opt in to the downgrade, and only via `server/discover`.

## What each revision removed / added

| Feature | 2025-06-18 | 2025-11-25 | 2026-07-28 |
|---------|------------|------------|------------|
| `initialize` handshake | present | present | **removed** |
| `Mcp-Session-Id` | present | present | **removed** |
| Streamable HTTP sessions | n/a | optional | **removed** (stateless only) |
| SSE resumability / `Last-Event-ID` | n/a | present | **removed** |
| Per-request `_meta` | optional | optional | **MUST on every request** |
| `server/discover` | MAY | MAY | **MUST** |
| Tasks in core (`tasks/result`, `tasks/list`) | absent | present (experimental) | **removed from core** |
| Tasks extension (`io.modelcontextprotocol/tasks`) | absent | absent | present |
| `resultType` / MRTR | absent | absent | present |
| Dynamic Client Registration | supported | supported | **deprecated** |
| Client ID Metadata Documents | absent | absent | recommended |
| Roots / Sampling / Logging | supported | supported | **deprecated** |
| HTTP+SSE transport | supported | supported | **deprecated** |
| Error code `-32022` | absent | absent | UnsupportedProtocolVersion |
| Error code `-32021` | absent | absent | MissingRequiredClientCapability |

## Concrete breakage scenarios (worked examples)

**Bad — shipping a 2025-06-18 server as-is.** A 2026-07-28 client sends its first
request with `_meta` and no `initialize`. The old server waits for `initialize`,
times out, and returns `-32603`. Detection: the server log shows it never saw a
`initialize` call. Fix: run `server/discover` first; if the server does not
advertise `2026-07-28`, either upgrade it or pin the client to the server's version
in config — never in logic.

**Bad — client hardcodes `"2026-07-28"` in source.** The next revision ships and
the client keeps talking a removed revision. Detection: grep the codebase for the
literal; every hit must be behind a config/env read. Fix: read from
`MCP_PROTOCOL_VERSION`, validate against the vendored list, fail fast on unknown.

**Bad — client assumes `tasks/result` exists.** SEP-1686 (2025-11-25) had it;
2026-07-28 removed it. Detection: any code calling `tasks/result` returns
`-32601` Method not found. Fix: poll with `tasks/get`, send input with `tasks/update`.

**Good — version-pinned, discover-first.** Client reads `MCP_PROTOCOL_VERSION`
(default `2026-07-28`), calls `server/discover`, intersects the two version lists,
picks the highest common, and stores the agreed revision in a typed config object.
All subsequent requests carry that revision in `_meta`. If the intersection is
empty, the client refuses with `-32022` and reports the incompatibility — it never
guesses a version.
