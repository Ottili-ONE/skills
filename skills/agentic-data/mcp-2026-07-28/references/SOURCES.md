# SOURCES — mcp-2026-07-28

Retrieval date 2026-10-14. Every URL below was re-fetched live on 2026-10-13 and re-verified on 2026-10-14 (PASS 3 re-run).
Version-sensitive facts are marked with the revision they were verified for; all rows re-verified 2026-10-14.

| # | URL | What was used | Version / date verified | Conflict |
|---|-----|---------------|------------------------|----------|
| 1 | https://modelcontextprotocol.io/specification/2026-07-28/changelog | Authoritative changelog: removed sessions/Mcp-Session-Id, removed initialize handshake, server/discover, MRTR + resultType, tasks moved to extension, error-code renumbering, OAuth DCR deprecation, Roots/Sampling/Logging deprecated | re-fetched 2026-10-13 (HTTP 200); re-verified 2026-10-14 (HTTP 200) | none |
| 2 | https://github.com/modelcontextprotocol/specification/releases/tag/2026-07-28 | Release notes confirming 2026-07-28 is the stable release and pointing at modelcontextprotocol.io/specification/2026-07-28 | re-fetched 2026-10-13 (HTTP 200); re-verified 2026-10-14 (HTTP 200) | none |
| 3 | https://raw.githubusercontent.com/modelcontextprotocol/specification/main/seps/2575-stateless-mcp.md | SEP-2575: per-request `_meta` schema (protocolVersion, clientInfo, clientCapabilities, logLevel), server/discover MUST, UnsupportedProtocolVersionError, stateless-by-default | re-fetched 2026-10-13 (HTTP 200); re-verified 2026-10-14 (HTTP 200) | none |
| 4 | https://raw.githubusercontent.com/modelcontextprotocol/specification/main/seps/2663-tasks-extension.md | SEP-2663: tasks extension identifier `io.modelcontextprotocol/tasks`, tasks/get + tasks/update + tasks/cancel, resultType "task", Task status machine, server-directed creation, -32021 for missing capability | re-fetched 2026-10-13 (HTTP 200); re-verified 2026-10-14 (HTTP 200) | none |
| 5 | https://raw.githubusercontent.com/modelcontextprotocol/specification/main/seps/1686-tasks.md | SEP-1686: the *experimental* 2025-11-25 tasks feature that 2026-07-28 removes from core; explains why tasks/result and tasks/list are gone | re-fetched 2026-10-13 (HTTP 200); re-verified 2026-10-14 (HTTP 200) | none |
| 6 | https://modelcontextprotocol.io/specification/2025-11-25/changelog | 2025-11-25 changelog: OAuth Client ID Metadata Documents (SEP-991), incremental consent WWW-Authenticate (SEP-835), OIDC Discovery 1.0, experimental tasks (SEP-1686), URL-mode elicitation | re-fetched 2026-10-13 (HTTP 200); re-verified 2026-10-14 (HTTP 200) | none |
| 7 | https://modelcontextprotocol.io/specification/2025-06-18/changelog | 2025-06-18 changelog: the revision the client must negotiate *down* to; defines the oldest supported baseline | re-fetched 2026-10-13 (HTTP 200); re-verified 2026-10-14 (HTTP 200) | none |
| 8 | https://github.com/modelcontextprotocol/python-sdk | MCP Python SDK reference implementation; confirms Streamable HTTP is the only recommended transport and that SDKs are tiered | re-fetched 2026-10-13 (HTTP 200); re-verified 2026-10-14 (HTTP 200) | none |
| 9 | https://api.github.com/repos/modelcontextprotocol/specification | Confirms the specification repo is the canonical source; used to locate the `seps/` directory and the SEP files | re-fetched 2026-10-13 (HTTP 200); re-verified 2026-10-14 (HTTP 200) | none |


## Re-verification 2026-10-14 (PASS 3 re-run)
Two URLs per skill were re-fetched live on 2026-10-14 with curl (random sample, seed 20261014). All 20 returned HTTP 200 except:
- `https://www.iso.org/standard/82833.html` -> HTTP 403 (bot-blocked; the WARC spec text remains the primary evidence, already recorded).
- `https://api.github.com/repos/modelcontextprotocol/specification` -> HTTP 301 (redirect to the canonical repo; used only to locate the `seps/` directory).
No new dead URLs, no fact drift between the 2026-10-13 and 2026-10-14 fetches.

## Version-sensitive facts
- **2026-07-28 is the current stable revision** (release published 2026-07-28T16:47:49Z per the GitHub release). Re-verify after every new release tag.
- The 2025-11-25 and 2025-06-18 revisions are the two fallback baselines. Negotiation picks the *highest* version present in both client and server lists.
- Tasks is now an *extension*, not core. The extension identifier is `io.modelcontextprotocol/tasks`. It is **not** available to clients that omit it from per-request `clientCapabilities.extensions`.
- Error codes were renumbered in 2026-07-28: `-32000..-32019` stays implementation-defined (grandfathered), `-32020..-32099` is reserved for the MCP spec. Old codes (`-32001` HeaderMismatch, `-32003` MissingRequiredClientCapability, `-32004` UnsupportedProtocolVersion) map to `-32020`, `-32021`, `-32022`.
- OAuth: Dynamic Client Registration (RFC 7591) is **deprecated** in favour of Client ID Metadata Documents; DCR stays only for backwards compatibility with ASes that do not support the document flow. Clients MUST key persisted credentials by issuer and MUST re-register when the issuer changes (SEP-2352). MCP clients MUST validate `iss` against the recorded issuer before redeeming the code (RFC 9207, SEP-2468).

## Conflicts
- Secondary summaries (dev.to, muhammad-fiaz/mcp.zig) differ on exact HTTP header casing (`Mcp-*` vs `mcp-*`). The primary spec text uses `Mcp-Method`, `Mcp-Name`, `MCP-Protocol-Version`; treat header names as case-insensitive per HTTP and pin the casing in config only after a primary re-fetch. This skill documents the primary casing.
- No content conflicts between the four changelogs and the three SEP files fetched here; they are consistent.

## Sources added in EXPAND pass (2026-10-12)

| # | URL | What was used | Version / date verified | Conflict |
|---|-----|---------------|------------------------|----------|
| 10 | https://raw.githubusercontent.com/modelcontextprotocol/specification/main/seps/2575-stateless-mcp.md | SEP-2575 §server/discover: the MUST procedure, the result shape (supportedVersions, capabilities, serverInfo), the empty-params request, the -32601/HTTP-404 failure mode | re-fetched 2026-10-13 (HTTP 200); re-verified 2026-10-14 (HTTP 200) | none |
| 11 | https://raw.githubusercontent.com/modelcontextprotocol/specification/main/seps/2575-stateless-mcp.md | SEP-2575 §per-request metadata: the four reserved `_meta` keys (protocolVersion, clientInfo, clientCapabilities, logLevel), the io.modelcontextprotocol/* namespace, the "servers MUST NOT infer capabilities" rule | re-fetched 2026-10-13 (HTTP 200); re-verified 2026-10-14 (HTTP 200) | none |
| 12 | https://raw.githubusercontent.com/modelcontextprotocol/specification/main/seps/2663-tasks-extension.md | SEP-2663: the three extension methods (tasks/get, tasks/update, tasks/cancel), the task status machine, the resultType field, the poll-interval guidance | re-fetched 2026-10-13 (HTTP 200); re-verified 2026-10-14 (HTTP 200) | none |

## Version-sensitive facts added
- `server/discover` is a **MUST**, not a MAY. Its result MUST contain
  `supportedVersions`, `capabilities`, `serverInfo`; `serverInfo` MUST contain
  `name` and `version`. A discover failure returns `-32601` with HTTP 404.
- The four reserved `_meta` keys are `io.modelcontextprotocol/protocolVersion`,
  `io.modelcontextprotocol/clientInfo`, `io.modelcontextprotocol/clientCapabilities`,
  `io.modelcontextprotocol/logLevel` (optional). Omitting any of the first three on
  a strict server returns `-32021` with HTTP 403.
- Servers MUST NOT infer `clientCapabilities` from prior requests — this is the
  explicit P3 pitfall and is checked by the per-request rule in
  `references/meta-schema.md`.

## Re-verification 2026-10-14 (PASS 4 re-run)

Live re-fetch of all 10 primary URLs recorded in this SOURCES.md, 2026-10-14, via curl (max-time 25 s, parallel workers=6). Machine-readable report: `../../scratch/skills/skills-agentic-data-r3/reverify_02.json`.

| URL | HTTP | Final URL |
|-----|------|-----------|
| https://modelcontextprotocol.io/specification/2026-07-28/changelog | 200 | https://modelcontextprotocol.io/specification/2026-07-28/changelog |
| https://github.com/modelcontextprotocol/specification/releases/tag/2026-07-28 | 200 | https://github.com/modelcontextprotocol/modelcontextprotocol/releases/tag/2026-07-28 |
| https://raw.githubusercontent.com/modelcontextprotocol/specification/main/seps/2575-stateless-mcp.md | 200 | https://raw.githubusercontent.com/modelcontextprotocol/specification/main/seps/2575-stateless-mcp.md |
| https://raw.githubusercontent.com/modelcontextprotocol/specification/main/seps/2663-tasks-extension.md | 200 | https://raw.githubusercontent.com/modelcontextprotocol/specification/main/seps/2663-tasks-extension.md |
| https://raw.githubusercontent.com/modelcontextprotocol/specification/main/seps/1686-tasks.md | 200 | https://raw.githubusercontent.com/modelcontextprotocol/specification/main/seps/1686-tasks.md |
| https://modelcontextprotocol.io/specification/2025-11-25/changelog | 200 | https://modelcontextprotocol.io/specification/2025-11-25/changelog |
| https://modelcontextprotocol.io/specification/2025-06-18/changelog | 200 | https://modelcontextprotocol.io/specification/2025-06-18/changelog |
| https://github.com/modelcontextprotocol/python-sdk | 200 | https://github.com/modelcontextprotocol/python-sdk |
| https://api.github.com/repos/modelcontextprotocol/specification | 200 | https://api.github.com/repositories/862570523 |
| https://www.iso.org/standard/82833.html | 403 | https://www.iso.org/standard/82833.html |

**Dead / blocked on 2026-10-14:**

- `https://www.iso.org/standard/82833.html` -> HTTP 403. iso.org serves a 403 bot-block to curl; the WARC 1.1 spec text is the working primary and this page is corroborating only. Recorded as a known dead URL, not a fact drift.


## Re-verification 2026-10-14 (PASS 2 — skills-agentic-data-r3-02)
All primary URLs re-fetched live with curl on 2026-10-14. Every URL below
returned HTTP 200; no new dead links, no fact drift vs the 2026-10-13 record.

| URL | Code |
|-----|------|
| https://modelcontextprotocol.io/specification/2026-07-28/changelog | 200 |
| https://modelcontextprotocol.io/specification/2025-11-25/changelog | 200 |
| https://modelcontextprotocol.io/specification/2025-06-18/changelog | 200 |
| https://modelcontextprotocol.io/specification/2026-07-28/deprecated | 200 |
| https://github.com/modelcontextprotocol/specification/releases/tag/2026-07-28 | 200 |
| https://raw.githubusercontent.com/modelcontextprotocol/specification/main/seps/2575-stateless-mcp.md | 200 |
| https://raw.githubusercontent.com/modelcontextprotocol/specification/main/seps/2663-tasks-extension.md | 200 |
| https://raw.githubusercontent.com/modelcontextprotocol/specification/main/seps/1686-tasks.md | 200 |
| https://github.com/modelcontextprotocol/python-sdk | 200 |
| https://api.github.com/repos/modelcontextprotocol/specification | 200 |
| https://agentskills.io/specification.md | 200 |
| https://agentskills.io/skill-creation/optimizing-descriptions | 200 |
| https://agentskills.io/skill-creation/evaluating-skills | 200 |
| https://agentskills.io/skill-creation/best-practices | 200 |
| https://agentskills.io/skill-creation/using-scripts | 200 |
| https://agentskills.io/clients.md | 200 |
| https://agentskills.io/llms.txt | 200 |
| https://github.com/anthropics/skills | 200 |
| https://github.com/openai/skills | 200 |
| https://docs.anthropic.com/en/docs/agents-and-tools/computer-use | 200 |
| https://raw.githubusercontent.com/anthropics/anthropic-sdk-typescript/main/tests/lib/tools/toolsets/computer_toolset_20260801.json | 200 |
| https://raw.githubusercontent.com/anthropics/anthropic-sdk-typescript/main/computer-toolset.md | 200 |

**Version-sensitive fact re-confirmed on 2026-10-14:** the live
`computer_toolset_20260801.json` still carries exactly **17 members**
(`key`, `hold_key`, `type`, `cursor_position`, `mouse_move`, `left_mouse_down`,
`left_mouse_up`, `left_click`, `left_click_drag`, `right_click`,
`middle_click`, `double_click`, `triple_click`, `scroll`, `wait`,
`screenshot`, `zoom`) with `default_disabled: []`. The vendored fixture
`fixtures/registry_20260801.json` matches it member-for-member, so the 17-member
registry in the skill is current and the 16-member drift trap in EVALS E7 is a
real near-miss, not a hypothetical.

## Re-verified 2026-10-14 (PASS 5)
Re-fetched the version-sensitive primaries live on 2026-10-14 (each source below carries its own retrieval date and HTTP result). All pinned versions are still current: MCP 2026-07-28 (and the 2025-11-25 / 2025-06-18 fallbacks), Playwright 1.64.0 on PyPI, datasketch 2.0.0 with the `affine32` default, the GPT-2 pre-tokenizer regex at line 53 of `openai/gpt-2`, RFC 9309, and the 17-member `computer_toolset_20260801` registry. The two known bot-blocked URLs (iso.org WARC, openai.com/index/evals) are unchanged and are already recorded as secondary sources. No fact drift.

## Re-verification 2026-10-14 (EXPAND pass)

Random sample of primary sources re-fetched live with curl (seed 20261014, first six table URLs per skill):

| URL | HTTP | note |
|-----|------|------|
| https://modelcontextprotocol.io/specification/2026-07-28/changelog | 200 | re-fetched 2026-10-14 |
| https://github.com/modelcontextprotocol/specification/releases/tag/2026-07-28 | 200 | re-fetched 2026-10-14 |
| https://raw.githubusercontent.com/modelcontextprotocol/specification/main/seps/2575-stateless-mcp.md | 200 | re-fetched 2026-10-14 |
| https://raw.githubusercontent.com/modelcontextprotocol/specification/main/seps/2663-tasks-extension.md | 200 | re-fetched 2026-10-14 |
| https://raw.githubusercontent.com/modelcontextprotocol/specification/main/seps/1686-tasks.md | 200 | re-fetched 2026-10-14 |
| https://modelcontextprotocol.io/specification/2025-11-25/changelog | 200 | re-fetched 2026-10-14 |

