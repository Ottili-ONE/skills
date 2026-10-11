# MCP changelog — vendored revision table

Retrieval 2026-10-12. Source: modelcontextprotocol.io specification changelogs.
This file is the **vendored allowed list** that `scripts/protocol_check.py` and
`scripts/version_negotiate.py` validate against. Update it via PR review when a
new revision ships; scripts never fetch remote URLs at runtime.

| Revision | Status | Release date | Role in this skill |
|----------|--------|--------------|--------------------|
| 2026-07-28 | **latest / primary** | 2026-07-28 | Target revision. Stateless, server/discover, MRTR, tasks extension, OAuth 2.1 + Client ID Metadata Documents. |
| 2025-11-25 | supported fallback | 2025-11-25 | Negotiate down to this. Has initialize handshake, Mcp-Session-Id, experimental tasks (tasks/result, tasks/list). |
| 2025-06-18 | oldest supported baseline | 2025-06-18 | Floor. Anything older is refused with UnsupportedProtocolVersionError (-32022). |
| 2025-03-26 | deprecated | 2025-03-26 | HTTP+SSE transport is deprecated; refuse or migrate to Streamable HTTP. |

## Negotiation rule (implemented in version_negotiate.py)
```
agreed = max(v for v in (client_versions ∩ server_versions) if v in ALLOWED)
```
If the intersection is empty, return FAIL with `-32022` (UnsupportedProtocolVersion)
and the server's `supported` list from `server/discover`. Never silently pick a
lower-than-supported version that weakens security — refuse instead.
