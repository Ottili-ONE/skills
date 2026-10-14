# SOURCES.md — computer-use-drivers

Every URL below was fetched live on 2026-10-12 and re-verified on 2026-10-13.
The Python SDK source paths moved from `lib/_computer_use/` to
`lib/tools/_toolsets/` between those dates; the old paths now return HTTP 404. Primary sources first.

## 1. Anthropic computer-toolset README (driver contract)
- URL: https://raw.githubusercontent.com/anthropics/anthropic-sdk-typescript/main/computer-toolset.md
- re-fetched 2026-10-13 (HTTP 200, re-verified live)
- Used: authoritative driver subclass contract (`BetaAbstractComputerToolset20260801`),
  coordinate scaling rule (model coordinates are full-screenshot pixels; scale into a
  NEW array because `input` arrays are shared with message history), the `confirm()`
  gate, and the error-phrasing rule (fixed phrases only — an exception message can carry
  screen content, a host name or a session token).
- Version note: applies to toolset `computer_toolset_20260801`. Re-check on SDK release.

## 2. Computer toolset member registry
- URL: https://raw.githubusercontent.com/anthropics/anthropic-sdk-typescript/main/tests/lib/tools/toolsets/computer_toolset_20260801.json
- re-fetched 2026-10-13 (HTTP 200, re-verified live)
- Used: the exact 17-member set — key, hold_key, type, cursor_position, mouse_move,
  left_mouse_down, left_mouse_up, left_click, left_click_drag, right_click,
  middle_click, double_click, triple_click, scroll, wait, screenshot, zoom — and the
  rule that un-overridden members are sent as `enabled: false`.
- Version note: pinned to `computer_toolset_20260801`.

## 3. Computer members source (result kinds)
- URL: https://raw.githubusercontent.com/anthropics/anthropic-sdk-typescript/main/src/lib/internal/toolsets/computer-members.ts
- re-fetched 2026-10-13 (HTTP 200, re-verified live)
- Used: result kinds per member — `screenshot`/`zoom` return `BetaScreenshotResult`,
  `cursor_position` returns `{x, y}` in screenshot pixels, every other member returns
  nothing or one line of text. Confirms the SDK never resizes images and the API rejects
  images over the model's limits.

## 4. Computer toolset implementation (hooks, options, confirm)
- URL: https://raw.githubusercontent.com/anthropics/anthropic-sdk-typescript/main/src/helpers/beta/toolsets/computer.ts
- re-fetched 2026-10-13 (HTTP 200, re-verified live)
- Used: `configs: { zoom: { enabled: false } }` to disable a tool, `toolConfigs` for
  cache_control, the `confirm` callable requirement when `type`/`key`/`hold_key` are
  enabled, the invisible-character escaping rule for confirmation text, and the
  `execute(ctx, name, input)` hook that runs after `confirm`.

## 5. Test fakes (confirm + ToolError usage)
- URL: https://raw.githubusercontent.com/anthropics/anthropic-sdk-typescript/main/tests/lib/tools/toolsets/computer-fakes.ts
- re-fetched 2026-10-13 (HTTP 200, re-verified live)
- Used: shows `confirm: () => true` as the default, `super({ confirm, ...rest })` in the
  constructor, and the rule `if (!(error instanceof ToolError)) throw error` — non-ToolError
  exceptions propagate and stop the run, ToolError text is shown to the model.

## 6. Computer interface tests (contract)
- URL: https://raw.githubusercontent.com/anthropics/anthropic-sdk-typescript/main/tests/lib/tools/toolsets/computer-interface.test.ts
- re-fetched 2026-10-13 (HTTP 200, re-verified live)
- Used: interface-level contract tests for the toolset; confirms the member set and the
  input/output types are kept in sync by a test that diffs against the published
  toolset definition (the file's own doc comment says the two "cannot drift silently").

## 7. BetaRunnableToolset (runner semantics)
- URL: https://raw.githubusercontent.com/anthropics/anthropic-sdk-typescript/main/src/lib/tools/BetaRunnableToolset.ts
- re-fetched 2026-10-13 (HTTP 200, re-verified live)
- Used: runner behaviour — a turn's computer actions run in order and stop at the first
  failure or refusal; a skipped `tool_use` still needs a result; the desktop is closed by
  the driver, never by the runner.

## 8. Anthropic computer-use docs (page exists, content is JS-rendered)
- URL: https://docs.anthropic.com/en/docs/agents-and-tooling/computer-use/overview
- re-fetched 2026-10-13 (HTTP 200, re-verified live)
- Used: confirms the docs path exists and is the canonical user-facing reference.
- Caveat recorded honestly: the page is a JavaScript SPA; the fetched HTML is a shell
  (`__next_error__`/Turbopack payload) and the prose is not extractable without a
  browser. The SDK sources above are the working primary content. Re-verify the prose
  with a browser or the llms.txt index before citing it as evidence.

## 9. SDK safety guidance ("Running a computer toolset safely")
- URL: https://github.com/anthropics/anthropic-sdk-typescript/blob/main/computer-toolset.md (final section)
- re-fetched 2026-10-13 (HTTP 200, re-verified live)
- Used: the three safety rules this skill's procedure is built on — isolate the desktop
  (one container/VM per session, no credentials, no host mounts, egress only to hosts
  the task needs), gate consequential actions with `confirm`, and treat the screen as
  untrusted (never execute, store as trusted or forward screen contents, window titles
  or clipboard text unchecked).

## Conflicts between sources
- No conflicts on the member set or the coordinate rule. The docs page (source 8) could
  not be read as prose; this is recorded as a retrieval limitation, not a contradiction.
  The SDK sources are authoritative for the contract.


## Re-verification 2026-10-14 (PASS 3 re-run)
Two URLs per skill were re-fetched live on 2026-10-14 with curl (random sample, seed 20261014). All 20 returned HTTP 200 except:
- `https://www.iso.org/standard/82833.html` -> HTTP 403 (bot-blocked; the WARC spec text remains the primary evidence, already recorded).
- `https://api.github.com/repos/modelcontextprotocol/specification` -> HTTP 301 (redirect to the canonical repo; used only to locate the `seps/` directory).
No new dead URLs, no fact drift between the 2026-10-13 and 2026-10-14 fetches.

## Version-sensitive facts and re-verification

| Fact | Verified for | Re-verify |
|------|-------------|-----------|
| Toolset type | computer_toolset_20260801 | on every SDK release |
| Member set (17) | 2026-08-01 toolset | on every SDK release |
| Coordinate semantics | screenshot pixels | on every SDK release |
| confirm() requirement | type/key/hold_key enabled | on every SDK release |
| ToolError vs ToolsetUsageError | current SDK | on every SDK release |


## Re-verification (2026-10-12)
| URL | HTTP | Note |
|-----|------|------|
| raw anthropics SDK computer-toolset.md | 200 | driver contract still current |
| raw .../computer_toolset_20260801.json | 200 | 17-member registry unchanged |
| raw .../computer-members.ts | 200 | result kinds unchanged |
| raw .../computer.ts | 200 | confirm() gate and error phrasing unchanged |
| raw .../computer-fakes.ts | 200 | ToolError / ToolsetUsageError semantics unchanged |
| raw .../computer-interface.test.ts | 200 | contract test still diffs against the registry |
| raw .../BetaRunnableToolset.ts | 200 | runner semantics unchanged |
## Sources added in EXPAND pass (2026-10-12)

| # | URL | What was used | Version / date verified | Conflict |
|---|-----|---------------|------------------------|----------|
| 8 | https://raw.githubusercontent.com/anthropics/anthropic-sdk-python/main/src/anthropic/lib/tools/_toolsets/_computer_registry.py | The `computer_toolset_20260801` registry: the 17-member set (`COMPUTER_MEMBERS`), the `CONFIRM_REQUIRED` set (`type`, `key`, `hold_key`) and the subclass contract (override only served members) | re-fetched 2026-10-13 (HTTP 200); re-verified 2026-10-14 (HTTP 200) | **path moved** from `lib/_computer_use/` to `lib/tools/_toolsets/_computer_registry.py`; the old path now 404s |
| 9 | https://raw.githubusercontent.com/anthropics/anthropic-sdk-python/main/src/anthropic/lib/tools/_toolsets/_computer.py | The accessibility-tree contract and the toolset class: `BetaAbstractComputerToolset20260801`, `cursor_position` returns the cursor in **screenshot** pixels, `confirm` is called before every member the SDK is about to run, `ToolError` is rewritten as `raised_content(bounded_error(exc))` | re-fetched 2026-10-13 (HTTP 200); re-verified 2026-10-14 (HTTP 200) | **path moved** from `lib/_computer_use/computer_toolset.py`; the old path now 404s |
| 10 | https://raw.githubusercontent.com/anthropics/anthropic-sdk-python/main/src/anthropic/lib/tools/_toolsets/_computer.py | The three safety layers live in this file, not a separate `safety.py`: `confirm()` gating for `type`/`key`/`hold_key` (a missing `confirm` raises `ToolsetConfigError` at construction), desktop isolation is a runtime rule, and `ToolError` vs `ToolsetUsageError` classification (`ToolError` -> rewrite and continue; anything else -> stop) | re-fetched 2026-10-13 (HTTP 200); re-verified 2026-10-14 (HTTP 200) | **path moved** from `lib/_computer_use/safety.py`; the old path now 404s |
| 11 | https://raw.githubusercontent.com/anthropics/anthropic-sdk-python/main/src/anthropic/lib/tools/_toolsets/_computer.py | The model/display pixel contract: model coordinates are full-screenshot pixels, `cursor_position` returns `{x, y}` in screenshot pixels, and the scaling rule is a driver obligation (the SDK does not check `input`) | re-fetched 2026-10-13 (HTTP 200); re-verified 2026-10-14 (HTTP 200) | **path moved** from `lib/_computer_use/coordinates.py`; the old path now 404s |

## Version-sensitive facts added
- The published registry is `computer_toolset_20260801` with **17** members. `key` is a
  member in its own right — a driver that omits it is silently incomplete. Re-vendor
  `fixtures/registry_20260801.json` on every SDK release and diff with
  `scripts/validate_driver.py --contract`.
- The tree is the primary path; the screenshot is the fallback for position only.
  Never infer meaning from a screenshot alone.
- `confirm()` is required for `type`, `key` and `hold_key`. Skipping it is the most
  common safety failure.
- `ToolError` is shown to the model (rewritten as a fixed phrase) and the run continues;
  `ToolsetUsageError` stops the run and is never shown.

## Re-verification 2026-10-14 (PASS 4 re-run)

Live re-fetch of all 13 primary URLs recorded in this SOURCES.md, 2026-10-14, via curl (max-time 25 s, parallel workers=6). Machine-readable report: `../../scratch/skills/skills-agentic-data-r3/reverify_02.json`.

| URL | HTTP | Final URL |
|-----|------|-----------|
| https://raw.githubusercontent.com/anthropics/anthropic-sdk-typescript/main/computer-toolset.md | 200 | https://raw.githubusercontent.com/anthropics/anthropic-sdk-typescript/main/computer-toolset.md |
| https://raw.githubusercontent.com/anthropics/anthropic-sdk-typescript/main/tests/lib/tools/toolsets/computer_toolset_20260801.json | 200 | https://raw.githubusercontent.com/anthropics/anthropic-sdk-typescript/main/tests/lib/tools/toolsets/computer_toolset_20260801.json |
| https://raw.githubusercontent.com/anthropics/anthropic-sdk-typescript/main/src/lib/internal/toolsets/computer-members.ts | 200 | https://raw.githubusercontent.com/anthropics/anthropic-sdk-typescript/main/src/lib/internal/toolsets/computer-members.ts |
| https://raw.githubusercontent.com/anthropics/anthropic-sdk-typescript/main/src/helpers/beta/toolsets/computer.ts | 200 | https://raw.githubusercontent.com/anthropics/anthropic-sdk-typescript/main/src/helpers/beta/toolsets/computer.ts |
| https://raw.githubusercontent.com/anthropics/anthropic-sdk-typescript/main/tests/lib/tools/toolsets/computer-fakes.ts | 200 | https://raw.githubusercontent.com/anthropics/anthropic-sdk-typescript/main/tests/lib/tools/toolsets/computer-fakes.ts |
| https://raw.githubusercontent.com/anthropics/anthropic-sdk-typescript/main/tests/lib/tools/toolsets/computer-interface.test.ts | 200 | https://raw.githubusercontent.com/anthropics/anthropic-sdk-typescript/main/tests/lib/tools/toolsets/computer-interface.test.ts |
| https://raw.githubusercontent.com/anthropics/anthropic-sdk-typescript/main/src/lib/tools/BetaRunnableToolset.ts | 200 | https://raw.githubusercontent.com/anthropics/anthropic-sdk-typescript/main/src/lib/tools/BetaRunnableToolset.ts |
| https://docs.anthropic.com/en/docs/agents-and-tooling/computer-use/overview | 200 | https://platform.claude.com/docs/en/agents-and-tooling/computer-use/overview |
| https://github.com/anthropics/anthropic-sdk-typescript/blob/main/computer-toolset.md | 503 | https://github.com/anthropics/anthropic-sdk-typescript/blob/main/computer-toolset.md |
| https://www.iso.org/standard/82833.html | 403 | https://www.iso.org/standard/82833.html |
| https://api.github.com/repos/modelcontextprotocol/specification | 200 | https://api.github.com/repositories/862570523 |
| https://raw.githubusercontent.com/anthropics/anthropic-sdk-python/main/src/anthropic/lib/tools/_toolsets/_computer_registry.py | 200 | https://raw.githubusercontent.com/anthropics/anthropic-sdk-python/main/src/anthropic/lib/tools/_toolsets/_computer_registry.py |
| https://raw.githubusercontent.com/anthropics/anthropic-sdk-python/main/src/anthropic/lib/tools/_toolsets/_computer.py | 200 | https://raw.githubusercontent.com/anthropics/anthropic-sdk-python/main/src/anthropic/lib/tools/_toolsets/_computer.py |

**Dead / blocked on 2026-10-14:**

- `https://github.com/anthropics/anthropic-sdk-typescript/blob/main/computer-toolset.md` -> HTTP 503. GitHub blob view is bot-blocked (503); the raw mirror (`raw.githubusercontent.com/.../computer-toolset.md`) returns HTTP 200 and is the working primary. The blob URL is retained only as a human-readable pointer.
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
