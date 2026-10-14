# PASS 4 (RE-VERIFY) — skills-agentic-data-r3-02 — 2026-10-14

Scope: `skills/agentic-data/mcp-2026-07-28/`,
`skills/agentic-data/skill-authoring-evals/`,
`skills/agentic-data/computer-use-drivers/` (skills 1-3 of 10, agentic-data lane).

Goal: independent re-verification of the three shipped skills — validators,
scripts, tests, EVALS, front matter, and live re-fetch of every version-sensitive
primary URL. No new skill content is authored here; this pass records evidence
and fixes only what the re-verification finds.

## State at start
Tree clean apart from `long-test.log` (owned by another job, left uncommitted).
All three skills already committed under `skills-agentic-data-r3-01:` /
`skills-agentic-data-r3-02:` prefixes. SKILL.md bodies 137 / 110 / 172 lines.

## Verification run this pass (2026-10-14)
1. `python3 -m pytest skills/agentic-data/mcp-2026-07-28/ skills/agentic-data/skill-authoring-evals/ skills/agentic-data/computer-use-drivers/ -q` -> **64 passed**, 0 failed, 0 errors (5.4 s).
2. `python3 skills/agentic-data/scripts/acceptance_check.py` -> **ACCEPTANCE: PASS**; per-skill rows:
   - mcp-2026-07-28: 10 source URLs, DESIGN has trigger/procedure/scripts/evals, 9 eval prompts, SKILL.md 137 L, name == folder, description 457 chars, links resolve one level deep.
   - skill-authoring-evals: 12 source URLs, DESIGN has trigger/procedure/scripts/evals, 15 eval prompts, SKILL.md 110 L, name == folder, description 409 chars, links resolve one level deep.
   - computer-use-drivers: 13 source URLs, DESIGN has trigger/procedure/scripts/evals, 10 eval prompts, SKILL.md 172 L, name == folder, description 411 chars, links resolve one level deep.
3. `validate_skill.py` on each of the three: `29 0 0` / `21 0 0` / `22 0 0` (oks, fails, warns) — 0 fails, 0 warns.
4. Script smoke (real inputs, not just --help):
   - `version_negotiate.py --client "2026-07-28,2025-11-25" --server "2026-07-28,2025-06-18" --json` -> `{"agreed": "2026-07-28", "refused": null}`, rc 0.
   - `version_negotiate.py --client "2025-06-18" --server "2026-07-28"` -> `FAIL: no common version; server returns -32022 UnsupportedProtocolVersion`, stdout `0 1 0`, rc 1.
   - `protocol_check.py` empty stdin -> `FAIL: could not read input: input is empty`, rc 2; invalid JSON -> rc 2. Both honour the IO contract (machine counts to stdout, detail to stderr, non-zero on failure).
   - `eval_metrics.py --help`, `stateless_probe.py --help` -> rc 0.
5. **Live re-fetch 2026-10-14**: harness `../../scratch/skills/skills-agentic-data-r3/reverify_02.py` curled all 31 distinct primary URLs across the three SOURCES.md files (max-time 25 s, 6 parallel workers). 29 returned HTTP 200; 2 blocked:
   - `https://github.com/anthropics/anthropic-sdk-typescript/blob/main/computer-toolset.md` -> HTTP 503 (GitHub blob view bot-blocked). The raw mirror `raw.githubusercontent.com/.../computer-toolset.md` returns 200 and is the working primary; the blob URL is retained as a human-readable pointer only.
   - `https://www.iso.org/standard/82833.html` -> HTTP 403 (iso.org bot-blocks curl). Already recorded as a known dead URL in earlier passes; the WARC 1.1 spec text is the working primary.
   No fact drift between the 2026-10-13 and 2026-10-14 fetches; the `docs.anthropic.com` computer-use URL now redirects to `platform.claude.com` (HTTP 200 at target), which is a redirect, not a dead link.
6. Machine-readable report: `../../scratch/skills/skills-agentic-data-r3/reverify_02.json`.
