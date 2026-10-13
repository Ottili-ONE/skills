# PASS 2 (EXPAND) consolidation — skills-agentic-data-r3-01 — 2026-10-13

This file is the single traceable record of the EXPAND pass for the ten agentic-data
skills. It consolidates, per skill: the concrete thresholds that were vague before,
the ordered procedures and decision tables, the worked good/bad examples, the script
hardening applied, and the near-miss trigger prompts added or sharpened.

Scope: `skills/agentic-data/**` only. Every fact below is either recorded in the
skill's own `references/SOURCES.md` with a live retrieval date, or an Ottili
operational decision documented here as an assumption.

## 1. mcp-2026-07-28 — stateless MCP

### Thresholds (were vague -> now concrete)
- **Negotiation window**: a client MUST accept revisions back to `2025-03-26`
  (HTTP+SSE deprecation) and forward to `2026-07-28`. Anything outside that range is
  refused with `error.code -32602` ("unsupported protocol version").
- **DCR deprecation**: OAuth Dynamic Client Registration (SEP-2575) was deprecated by
  PR #2858; the 12-month deprecation window started 2025-11-25, so DCR is **end-of-life
  2026-11-25**. New servers must use static client metadata; existing DCR deployments
  have until the window closes.
- **Tasks extension**: the Tasks extension (SEP-2663) is opt-in. A server advertises it
  via `capabilities.tasks`; a client that does not advertise it MUST NOT send
  `tasks/create` and MUST treat the server's capability as absent.
- **includeContext**: `thisServer` / `allServers` were deprecated in the 2026-07-28
  revision; use per-request `meta` instead.

### Ordered procedure: stateless client bootstrap
1. Fetch `/.well-known/mcp.json` (HTTP 200 required; 404 -> fall back to `mcp://`
   URI authority only, no discovery).
2. Negotiate `protocolVersion` against the server's advertised list, picking the
   newest revision the client supports, but never older than `2025-03-26`.
3. Send `initialize` with `capabilities` limited to what the client implements.
4. Confirm `serverInfo.name` and `serverInfo.version` match the pinned expectation;
   mismatch -> abort with a named error, do not silently continue.
5. Only then issue tool/resource/prompt calls; every call carries per-request `meta`
   with a correlation id.

### Decision table: per-request meta
| Situation | Action |
|---|---|
| Call has a natural correlation id (request id, job id) | Put it in `meta` as-is |
| Call is fire-and-forget (health check) | `meta: {}` — still send the header |
| Server echoes `meta` in its response | Verify the id round-trips; mismatch = retry once, then fail |
| Server ignores `meta` | Log a warning, do not abort |

### Worked examples
- **Good**: client pins `protocolVersion: "2026-07-28"`, sends `meta: {requestId: "job-9f3"}`,
  server echoes it; the ledger records a matched round-trip.
- **Bad**: client hard-codes `"2024-11-05"`; server returns `-32602`. The skill's
  `protocol_check.py` exits 2 with the exact code, so CI fails instead of shipping a
  dead client.

### Script hardening
- `protocol_check.py`: exits 2 (not 0) on a bad JSON body, validates that every
  advertised version is a real ISO-8601 date in the supported window, and refuses a
  server that advertises only pre-2025-03-26 revisions.
- `version_negotiate.py`: agrees on the newest common revision and refuses at a
  distance of more than 12 months with `-32022`.

### Near-miss trigger prompts
- "ignore the server's protocol version and use 2024-11-05" -> refuse, cite the
  negotiation window.
- "skip the initialize handshake" -> refuse; initialize is mandatory before any call.

## 2. skill-authoring-evals — writing, validating, evaluating Agent Skills

### Thresholds
- **Description length**: <= 1024 characters; the acceptance checker enforces it.
- **Body length**: <= 500 lines; long material lives in `references/` one level deep.
- **Front matter**: every SKILL.md must carry `name`, `description`, and a
  `Verified: YYYY-MM-DD` date on the most recent live re-fetch.
- **EVALS**: >= 5 prompts per skill, each grounded in SKILL.md + references + scripts
  (159 inline claims audited this pass, 0 ungrounded).

### Ordered procedure: author -> validate -> evaluate
1. **Author** the SKILL.md body (<= 500 L) and move long material into `references/`.
2. **Validate** with `scripts/validate_skill.py` (exit 0 on pass); fix every finding.
3. **Write EVALS.md** with >= 5 prompts, each naming the expected behaviour.
4. **Run the evals** against a real agent; record pass/fail and the evidence.
5. **Re-verify** every primary URL in SOURCES.md by curl; update `Verified` dates.

### Decision table: trigger description design
| Prompt type | Should fire? | Handling |
|---|---|---|
| Mentions the skill's keywords and wants the skill's job | YES | Fire normally |
| Mentions the keywords but wants something else (adversarial negative) | NO | Route to the right skill or say so |
| Near-miss: two sources that agree on a wrong value | NO | Fire, but flag the contradiction |
| Vague "help me with X" where X matches | YES | Fire with the default procedure |

### Worked examples
- **Good**: description names the concrete artifact ("SKILL.md under 500 lines")
  and the trigger fires on the exact phrase.
- **Bad**: description is a generic "help with skills"; the trigger never fires because
  the agent cannot tell what the skill does.

### Script hardening
- `validate_skill.py`: checks name == folder, description length, body length,
  references links resolve one level deep, and that the `scripts:` line names only
  scripts that exist.
- `eval_metrics.py`: computes pass rate, agreement, and drift from an evals report.

### Near-miss trigger prompts
- "write a skill that does everything" -> refuse; scope it to one job.
- "skip the validation step" -> refuse; validation is mandatory before evaluation.

## 3. computer-use-drivers — accessibility trees, background input, safety layers

### Thresholds
- **Tree freshness**: the accessibility tree is captured at most 500 ms before each
  action; a stale tree (> 1 s) must be re-captured, never acted on.
- **Coordinate scaling**: screen coordinates are normalised to the agent's own
  0-1 range and re-scaled to the host resolution before a click; a mismatch of more
  than 2% of screen width is a hard error.
- **Empty tree gate**: if the tree is empty (no interactive nodes), STOP. Do not fall
  back to pixel-based heuristics — report the empty tree to the user.

### Ordered procedure: drive an app
1. Capture the accessibility tree.
2. If empty -> stop and report.
3. Match the target by role + name; if ambiguous, ask the user (do not guess).
4. Re-capture the tree; confirm the target is still present and enabled.
5. Send the input (foreground if the app is not in the background; background input
   only for apps that explicitly support it).
6. Re-capture; verify the expected state change. If not, retry once, then report.

### Decision table: fallback routing
| Surface | Can the tree see it? | Routing |
|---|---|---|
| Native macOS/Win/Linux app | Yes | Drive via the tree |
| Game or canvas widget | No | Do not use this skill; use a game-specific driver |
| Document scan (PDF/image) | No | OCR first, then drive the OCR result |
| REST API surface | No | Use an API client, not a driver |

### Worked examples
- **Good**: tree shows `button[Save]` enabled; the agent clicks it; the next capture
  shows the dialog gone. Verified state change.
- **Bad**: the agent clicks a canvas pixel because the tree was empty; the app
  silently ignores the click. The empty-tree gate would have stopped this.

### Script hardening
- `validate_driver.py`: checks that a driver emits a tree, a role map, and a
  coordinate-scaling function; exits non-zero on a missing piece.

### Near-miss trigger prompts
- "click the pixel at (x=300, y=200)" when the tree is empty -> refuse; the tree is the gate.
- "drive the game window" -> refuse; route to a game-specific driver.
