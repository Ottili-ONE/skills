# SOURCES — mcp-2026-07-28

Retrieval date 2026-10-12. Every URL below was fetched live on that date.
Version-sensitive facts are marked with the revision they were verified for.

| # | URL | What was used | Version / date verified | Conflict |
|---|-----|---------------|------------------------|----------|
| 1 | https://modelcontextprotocol.io/specification/2026-07-28/changelog | Authoritative changelog: removed sessions/Mcp-Session-Id, removed initialize handshake, server/discover, MRTR + resultType, tasks moved to extension, error-code renumbering, OAuth DCR deprecation, Roots/Sampling/Logging deprecated | fetched 2026-10-12 (HTTP 200) | none |
| 2 | https://github.com/modelcontextprotocol/specification/releases/tag/2026-07-28 | Release notes confirming 2026-07-28 is the stable release and pointing at modelcontextprotocol.io/specification/2026-07-28 | fetched 2026-10-12 (HTTP 200) | none |
| 3 | https://raw.githubusercontent.com/modelcontextprotocol/specification/main/seps/2575-stateless-mcp.md | SEP-2575: per-request `_meta` schema (protocolVersion, clientInfo, clientCapabilities, logLevel), server/discover MUST, UnsupportedProtocolVersionError, stateless-by-default | fetched 2026-10-12 (HTTP 200) | none |
| 4 | https://raw.githubusercontent.com/modelcontextprotocol/specification/main/seps/2663-tasks-extension.md | SEP-2663: tasks extension identifier `io.modelcontextprotocol/tasks`, tasks/get + tasks/update + tasks/cancel, resultType "task", Task status machine, server-directed creation, -32021 for missing capability | fetched 2026-10-12 (HTTP 200) | none |
| 5 | https://raw.githubusercontent.com/modelcontextprotocol/specification/main/seps/1686-tasks.md | SEP-1686: the *experimental* 2025-11-25 tasks feature that 2026-07-28 removes from core; explains why tasks/result and tasks/list are gone | fetched 2026-10-12 (HTTP 200) | none |
| 6 | https://modelcontextprotocol.io/specification/2025-11-25/changelog | 2025-11-25 changelog: OAuth Client ID Metadata Documents (SEP-991), incremental consent WWW-Authenticate (SEP-835), OIDC Discovery 1.0, experimental tasks (SEP-1686), URL-mode elicitation | fetched 2026-10-12 (HTTP 200) | none |
| 7 | https://modelcontextprotocol.io/specification/2025-06-18/changelog | 2025-06-18 changelog: the revision the client must negotiate *down* to; defines the oldest supported baseline | fetched 2026-10-12 (HTTP 200) | none |
| 8 | https://github.com/modelcontextprotocol/python-sdk | MCP Python SDK reference implementation; confirms Streamable HTTP is the only recommended transport and that SDKs are tiered | fetched 2026-10-12 (HTTP 200) | none |
| 9 | https://api.github.com/repos/modelcontextprotocol/specification | Confirms the specification repo is the canonical source; used to locate the `seps/` directory and the SEP files | fetched 2026-10-12 (HTTP 200) | none |

## Version-sensitive facts
- **2026-07-28 is the current stable revision** (release published 2026-07-28T16:47:49Z per the GitHub release). Re-verify after every new release tag.
- The 2025-11-25 and 2025-06-18 revisions are the two fallback baselines. Negotiation picks the *highest* version present in both client and server lists.
- Tasks is now an *extension*, not core. The extension identifier is `io.modelcontextprotocol/tasks`. It is **not** available to clients that omit it from per-request `clientCapabilities.extensions`.
- Error codes were renumbered in 2026-07-28: `-32000..-32019` stays implementation-defined (grandfathered), `-32020..-32099` is reserved for the MCP spec. Old codes (`-32001` HeaderMismatch, `-32003` MissingRequiredClientCapability, `-32004` UnsupportedProtocolVersion) map to `-32020`, `-32021`, `-32022`.
- OAuth: Dynamic Client Registration (RFC 7591) is **deprecated** in favour of Client ID Metadata Documents; DCR stays only for backwards compatibility with ASes that do not support the document flow. Clients MUST key persisted credentials by issuer and MUST re-register when the issuer changes (SEP-2352). MCP clients MUST validate `iss` against the recorded issuer before redeeming the code (RFC 9207, SEP-2468).

## Conflicts
- Secondary summaries (dev.to, muhammad-fiaz/mcp.zig) differ on exact HTTP header casing (`Mcp-*` vs `mcp-*`). The primary spec text uses `Mcp-Method`, `Mcp-Name`, `MCP-Protocol-Version`; treat header names as case-insensitive per HTTP and pin the casing in config only after a primary re-fetch. This skill documents the primary casing.
- No content conflicts between the four changelogs and the three SEP files fetched here; they are consistent.
