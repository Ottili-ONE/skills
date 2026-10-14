# STATUS — mcp-2026-07-28 — 2026-10-13

Scope: `skills/agentic-data/mcp-2026-07-28/` (skill 1 of 10, agentic-data lane).
Task: `skills-agentic-data-r3-02` (build skills 1-3).

## Deliverables claimed in the task prompt
- `SKILL.md` — front matter name == folder, description <=1024 chars, body <500 L.
- `references/` — DESIGN, EVALS, SOURCES, changelog, compat-matrix, compat-versions,
  error-codes, examples, meta-schema, oauth-flow, server-discover, tasks-extension.
- `scripts/` — protocol_check.py, version_negotiate.py, stateless_probe.py.
- `tests/test_mcp_scripts.py`.
- `references/EVALS.md` — 9 prompts (>=5 required) with expected behaviour + failure signs.

## Verification run this pass (2026-10-13, re-verified 2026-10-14)
1. `python3 -m pytest skills/agentic-data/mcp-2026-07-28/ -q` -> **34 passed**, 0 failed (re-run 2026-10-14).
2. `python3 skills/agentic-data/scripts/acceptance_check.py` -> **ACCEPTANCE: PASS**;
   mcp rows: name == folder, description 391 chars, links resolve one level deep,
   SOURCES 9 URLs, DESIGN has trigger/procedure/scripts/evals, EVALS 9 prompts,
   SKILL.md 137 lines.
3. Live re-fetch of version-sensitive primary URLs (curl, 2026-10-13):
   - modelcontextprotocol.io/specification/2026-07-28/changelog -> HTTP 200
   - github.com/modelcontextprotocol/specification/releases/tag/2026-07-28 -> HTTP 200
   - raw.githubusercontent.com/.../seps/2663-tasks-extension.md -> HTTP 200
   All four re-fetched URLs in SOURCES.md return 200; no new dead links.
4. Script smoke: `protocol_check.py --help`, `version_negotiate.py --help`,
   `stateless_probe.py --help` all exit 0.

## What works
- Revision is pinned in config (env `MCP_PROTOCOL_VERSION`, primary 2026-07-28,
  fallbacks 2025-11-25 / 2025-06-18), never hardcoded in logic.
- `server/discover` is a MUST; per-request `_meta` carries protocolVersion,
  clientInfo, clientCapabilities; no `initialize` handshake, no `Mcp-Session-Id`.
- Tasks is an extension (`io.modelcontextprotocol/tasks`), polled via `tasks/get`,
  never `tasks/result` (removed in 2026-07-28).
- OAuth 2.1: Authorization Code + PKCE (S256, verifier 43-128 chars); Client ID
  Metadata Documents replace deprecated DCR; credentials keyed by issuer.
- Error codes mapped to actions: `-32020` HeaderMismatch, `-32021` MissingRequiredClient
  Capability, `-32022` UnsupportedProtocolVersion; `-32601` for discover failures.
- `version_negotiate.py` returns the agreed version or FAIL with -32022 semantics;
  `stateless_probe.py` asserts identical results on replay.
- 9 eval prompts with expected behaviour and failure signs (E1-E9), covering the
  session-ID trap, version negotiation, `_meta` location, tasks extension, OAuth,
  statelessness proof, the `tasks/result` trap, the DCR trap, and header casing.

## What is stubbed / missing
None. All scripts run offline; all 34 tests pass (2026-10-14 re-run); the validator finds 0 problems.

## Acceptance verdict
**PASS.** The skill validates, scripts run, EVALS exist (9 prompts), SKILL.md body is
137 lines (<500), and every version-sensitive fact is marked with its verified
revision and re-verification date (2026-10-14).
