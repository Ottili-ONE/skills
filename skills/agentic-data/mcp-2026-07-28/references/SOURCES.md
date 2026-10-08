# SOURCES.md — mcp-2026-07-28

All URLs retrieved 2026-10-07 unless marked otherwise. Primary sources first.

## 1. Model Context Protocol specification, revision 2026-07-28
- URL: https://github.com/modelcontextprotocol/specification/releases/tag/2026-07-28
- Retrieved: 2026-10-07
- Used: authoritative changelog of the 2026-07-28 revision (12 major + 11 minor
  changes, deprecations, error-code renumbering). This is the single source of truth
  for what changed since 2025-11-25.
- Version note: applies to protocol version string `2026-07-28`. Re-verify at each
  spec release; the schema lives at `schema/2026-07-28/schema.ts`.

## 2. MCP specification docs — 2026-07-28/basic/index.mdx (general fields, `_meta`)
- URL: https://raw.githubusercontent.com/modelcontextprotocol/specification/main/docs/specification/2026-07-28/basic/index.mdx
- Retrieved: 2026-10-07
- Used: `_meta` reserved-key rules (`io.modelcontextprotocol/*` namespace),
  per-request protocol fields, error-code allocation policy.

## 3. MCP schema — schema/2026-07-28/schema.ts
- URL: https://raw.githubusercontent.com/modelcontextprotocol/specification/main/schema/2026-07-28/schema.ts
- Retrieved: 2026-10-07
- Used: `server/discover` request/result types, `RequestMetaObject`,
  `Extensions`/tasks extension keys, `resultType` field, `InputRequiredResult`.

## 4. MCP changelog — docs/specification/2026-07-28/changelog.mdx
- URL: https://raw.githubusercontent.com/modelcontextprotocol/specification/main/docs/specification/2026-07-28/changelog.mdx
- Retrieved: 2026-10-07
- Used: full list of breaking changes, including removal of `initialize` handshake,
  `Mcp-Session-Id`, `ping`, SSE resumability, and the tasks extension redesign.

## 5. developersdigest.tech — "MCP 2026-07-28 breaking changes"
- URL: https://www.developersdigest.tech/blog/mcp-2026-07-28-breaking-changes
- Retrieved: 2026-10-07
- Used: independent engineering write-up of the same breaking changes; used as a
  cross-check, not as authority. Agrees with the spec changelog on all major points.

## 6. jarvisbitztech — "MCP in 2026: what changed in the 2026-07-28 specification"
- URL: https://dev.to/jarvisbitztech/mcp-in-2026-what-changed-in-the-2026-07-28-specification-and-how-to-design-production-integrations-16c4
- Retrieved: 2026-10-07
- Used: production-integration guidance (statelessness, per-request metadata,
  version negotiation). Confirms `server/discover` is mandatory for servers.

## 7. MCP Go SDK releases
- URL: https://github.com/modelcontextprotocol/go-sdk/releases
- Retrieved: 2026-10-07
- Used: confirms Go SDK 1.7 pre-releases support 2026-07-28; used to pin the
  minimum SDK version in configuration, never in logic.

## 8. Vercel MCP Handler changelog
- URL: https://vercel.com/changelog/latest-mcp-spec-now-supported-in-mcp-handler
- Retrieved: 2026-10-07
- Used: confirms TypeScript SDK v2 (`@modelcontextprotocol/server`) support for the
  revision.

## 9. mcp.zig guide — protocol version
- URL: https://muhammad-fiaz.github.io/mcp.zig/guide/protocol-version.md
- Retrieved: 2026-10-07
- Used: confirms the three live protocol versions (2026-07-28, 2025-11-25,
  2025-06-18) and the negotiation-down rule.

## 10. R3_VERIFIED_FACTS.md (section 5, retrieved 2026-10-06)
- URL: /srv/ottili/repo/ottili-planning/inputs/R3_VERIFIED_FACTS.md
- Retrieved: 2026-10-07 (re-read)
- Used: starting point only; every fact above was re-verified against the primary
  spec sources on 2026-10-07.

## Conflicts between sources

- The verified-facts file lists the previous revisions as 2025-11-25 and 2025-06-18.
  The spec changelog confirms both dates exactly; no conflict.
- One secondary source (developersdigest) describes `server/discover` as optional
  for clients; the schema.ts docstring says clients **MAY** call it. The spec is
  authoritative: servers MUST implement it, clients MAY call it.
- The OAuth section of the verified-facts file mentions Dynamic Client Registration
  deprecation; the spec changelog confirms this (PR #2858) and adds the replacement
  (Client ID Metadata Documents). No conflict, just a newer detail.

## Version-sensitive facts and re-verification

| Fact | Verified for | Re-verify |
|------|-------------|-----------|
| Protocol version string | 2026-07-28 | at every spec release |
| Schema path | schema/2026-07-28/ | at every spec release |
| Go SDK support | 1.7 pre-release | when 1.7 ships |
| TypeScript SDK support | v2 | when the handler changelog updates |
| Error codes -32020..-32099 | 2026-07-28 | at every spec release |
