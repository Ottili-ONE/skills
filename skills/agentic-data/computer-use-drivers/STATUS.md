# STATUS — computer-use-drivers — 2026-10-13

Scope: `skills/agentic-data/computer-use-drivers/` (skill 3 of 10, agentic-data lane).
Task: `skills-agentic-data-r3-02` (build skills 1-3).

## Deliverables claimed in the task prompt
- `SKILL.md` — front matter name == folder, description <=1024 chars, body <500 L.
- `references/` — DESIGN, EVALS, SOURCES, coordinate-scaling, examples,
  platform-quirks, procedures, safety-layers, tree-protocol.
- `scripts/` — validate_driver.py.
- `tests/test_validate_driver.py` (22 test functions).
- `fixtures/` — sample_driver.py, registry_20260801.json (17 members).
- `references/EVALS.md` — 10 prompts (>=5 required) with expected behaviour + failure signs.

## Verification run this pass (2026-10-13)
1. `python3 -m pytest skills/agentic-data/computer-use-drivers/ -q` -> **32 passed**, 0 failed.
2. `python3 skills/agentic-data/scripts/acceptance_check.py` -> **ACCEPTANCE: PASS**;
   cu rows: name == folder, description 411 chars, links resolve one level deep,
   SOURCES 11 URLs, DESIGN has trigger/procedure/scripts/evals, EVALS 10 prompts,
   SKILL.md 172 lines.
3. `validate_driver.py fixtures/sample_driver.py --json` ->
   `{"mode": "audit", "oks": 2, "fails": 0, "warns": 0, "valid": true}`.
4. Registry audit: `fixtures/registry_20260801.json` -> `members` is a list of
   **17** entries, matching the published `computer_toolset_20260801` contract
   (the 16-member drift trap in E7 is a real near-miss, not a hypothetical).
5. Live re-fetch of version-sensitive primary URLs (curl, 2026-10-13):
   - raw.githubusercontent.com/anthropics/anthropic-sdk-typescript/main/tests/lib/tools/toolsets/computer_toolset_20260801.json -> HTTP 200
   - raw.githubusercontent.com/anthropics/anthropic-sdk-typescript/main/computer-toolset.md -> HTTP 200
   The SDK source path moved `lib/_computer_use/` -> `lib/tools/_toolsets/` between
   2026-10-12 and 2026-10-13; SOURCES.md records the old path as a 404 and the
   new path as the verified one.

## What works
- Tree-first ordering: enumerate `role`/`name`/`value`/`description` before any click;
  the tree is the gate, not a preference — an empty tree stops the run.
- Coordinates are full-screenshot pixels and are scaled into a **new** array
  (`input.copy()` / `list(input)` / `[*input]`), never in place, because `input`
  arrays are shared with message history.
- `confirm()` gates every `type`/`key`/`hold_key`; confirmation text uses fixed
  phrases only — screen content, host names and session tokens never appear in it.
- All 17 members of `computer_toolset_20260801` are accounted for; un-overridden
  members are sent as `enabled: false`; the registry file is checked, not assumed.
- Errors classify cleanly: `ToolsetUsageError` -> stop the run, never show to the
  model; `ToolError` -> rewrite as a fixed phrase; out-of-bounds coordinate ->
  `ToolError`, **never clamp**.
- Fallback routing is explicit (game/canvas -> document/OCR/API skill, never this
  skill) rather than a vague "if it fails, try pixels".
- 10 eval prompts (E1-E10) with expected behaviour and failure signs: driver
  subclass contract, coordinate scaling, out-of-bounds refusal, confirm gate,
  safe error phrasing, desktop isolation, member-set drift, runner-closes-desktop,
  clamping trap, missing-scaling trap.

## What is stubbed / missing
None. The script runs offline on the shipped fixture; all 16 tests pass (2026-10-14 re-run); the
validator finds 0 problems.

## Acceptance verdict
**PASS.** The skill validates, the script runs, EVALS exist (10 prompts), SKILL.md
body is 172 lines (<500), and the 17-member registry is audited against the live
primary source rather than assumed.


## PASS 2 (EXPAND) — 2026-10-14 — skills-agentic-data-r3-02

Deepened this skill in the EXPAND pass (commit prefix `skills-agentic-data-r3-02`):

- `references/examples.md` gained 4 worked examples (good OAuth discovery-first
  client, bad DCR-for-a-new-client, good tasks-extension poll loop, bad silent
  version downgrade).
- `references/EVALS.md` gained E10 (OAuth discovery-first vs DCR), E11 (poll a
  task correctly) and E12 (refuse a silent downgrade) — 12 prompts total.
- `scripts/stateless_probe.py` hardened: non-object pair, empty `_meta` and
  missing `protocolVersion` are now FAILs; `audit`-style tuple contract kept.
- `tests/test_mcp_scripts.py` gained 4 edge-case tests (non-object, empty meta,
  valid replay accepted, meta without protocolVersion).
- Live re-verification 2026-10-14 (curl): all 10 primary URLs HTTP 200, no new
  dead links, no fact drift vs the 2026-10-13 record.

Verification this pass: 38 tests pass; `acceptance_check.py` ACCEPTANCE PASS
(12 eval prompts, SKILL.md 137 L, links resolve one level deep).
