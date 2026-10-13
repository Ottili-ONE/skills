# Compatibility matrix — MCP revisions 2025-06-18 → 2026-07-28

Verified 2026-10-13 against the 2026-07-28 changelog (HTTP 200), the 2025-11-25
changelog (HTTP 200) and the 2025-06-18 changelog (HTTP 200). Every row below is a
**version-sensitive fact**: re-check after a new release tag.

## Per-revision feature matrix

| Feature | 2025-06-18 | 2025-11-25 | 2026-07-28 |
|---|---|---|---|
| Transport | HTTP+SSE, STDIO | HTTP+SSE, STDIO, Streamable HTTP | **Streamable HTTP only** (STDIO unchanged) |
| Sessions | `Mcp-Session-Id` on every response | same | **removed** — no session state |
| Handshake | `initialize` | `initialize` | **removed** — per-request `_meta` only |
| `server/discover` | absent | absent | **MUST**, returns `supportedVersions`/`capabilities`/`serverInfo` |
| Per-request `_meta` | absent | absent | 4 reserved keys on **every** request |
| Tasks | absent | experimental (SEP-1686): `tasks/result`, `tasks/list` | **extension** (SEP-2663): `tasks/get`, `tasks/update`, `tasks/cancel` |
| `resultType` | absent | absent | `complete` / `input_required` / `task` |
| OAuth | RFC 7591 DCR | Client ID Metadata Documents (SEP-991) + DCR | **DCR deprecated**, Metadata Documents required |
| `iss` validation | absent | absent | **MUST** before redeeming code (RFC 9207, SEP-2468) |
| Roots / Sampling / Logging | core | core | **deprecated** |
| `allowed-tools` | absent | absent | experimental metadata, never a hard gate |
| Error codes | `-32000..-32019` impl-defined | same, plus `-32001`/`-32003`/`-32004` | `-32000..-32019` grandfathered; **`-32020`/`-32021`/`-32022`** reserved |

## Code remapping (old → new)

| Old code (≤2025-11-25) | New code (2026-07-28) | Meaning |
|---|---|---|
| `-32001` | `-32020` | HeaderMismatch |
| `-32003` | `-32021` | MissingRequiredClientCapability |
| `-32004` | `-32022` | UnsupportedProtocolVersion |

A 2026-07-28 client that receives `-32001` from an old server must treat it as
`-32020`, not as an unknown implementation-defined code. `scripts/protocol_check.py`
maps both ranges.

## Negotiation thresholds (implemented in `version_negotiate.py`)

| Input | Behaviour |
|---|---|
| client ∩ server non-empty | pick `max(intersection ∩ ALLOWED)` — the **highest** common version |
| intersection empty | **refuse**, return `-32022` + server `supported` list |
| client sends a version not in `ALLOWED` | drop it from the candidate set, warn |
| duplicate version in a list | dedupe, warn once |

`ALLOWED` = `{2026-07-28, 2025-11-25, 2025-06-18}` from `references/changelog.md`.
Never silently pick a version lower than the highest common one — a downgrade
weakens security and loses `server/discover`.

## Deprecation deadlines (measured from deprecation revision)

| Feature | Deprecated in | Earliest removal revision |
|---|---|---|
| HTTP+SSE | 2025-03-26 | ≥ 2026-03-26 |
| Dynamic Client Registration | 2026-07-28 | ≥ 2027-07-28 |
| `includeContext` `thisServer`/`allServers` | 2026-07-28 | ≥ 2027-07-28 |
| Roots / Sampling / Logging | 2026-07-28 | ≥ 2027-07-28 |

Policy (feature-lifecycle, HTTP 200): the window is **at least twelve months**.
Treat the deadline as a hard removal date. Migrate now; log the deprecation.

## What a strong generic agent gets wrong

- Assuming `initialize` is still required — it was removed in 2026-07-28.
- Treating `Mcp-Session-Id` as optional — it is gone entirely.
- Calling `tasks/result` — removed; returns `-32601`.
- Using DCR for a new client — deprecated since 2026-07-28.
- Downgrading on a version mismatch — never; refuse with `-32022`.
