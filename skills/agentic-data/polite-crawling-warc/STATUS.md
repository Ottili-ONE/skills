# STATUS — polite-crawling-warc — 2026-10-14

Scope: `skills/agentic-data/polite-crawling-warc/` (skill 5 of 10, agentic-data lane).
Task: `skills-agentic-data-r3-03` (build skills 4-6).

## Deliverables claimed in the task prompt
- `SKILL.md` — front matter name == folder, description <=1024 chars, body <500 L.
- `references/` — DESIGN, EVALS, SOURCES, crawl-policy, warc-validation, procedures.
- `scripts/` — robots.py, rate_limit.py, resume_state.py, warc_writer.py,
  validate_warc.py, validate_skill.py.
- `tests/` — test_scripts.py, test_cli_edge.py.
- `references/EVALS.md` — 11 prompts (>=5 required) with expected behaviour + failure signs.

## Verification run this pass (2026-10-14, PASS 4 / r3-03 close-out)
1. `python3 -m pytest skills/agentic-data/polite-crawling-warc/ -q` -> **33 passed**, 0 failed.
2. `python3 skills/agentic-data/scripts/acceptance_check.py` -> **ACCEPTANCE: PASS**;
   polite rows: name == folder, description 337 chars, links resolve one level deep,
   SOURCES 13 URLs, DESIGN has trigger/procedure/scripts/evals, EVALS 11 prompts,
   SKILL.md 90 lines.
3. Per-skill validator: `scripts/validate_skill.py` -> **PASS: polite-crawling-warc
   validates against the Agent Skills standard**.
4. Script smoke (all six scripts, `--help`, exit 0): robots, rate_limit, resume_state,
   warc_writer, validate_warc, validate_skill.
5. Live re-fetch of version-sensitive primary URLs (curl, 2026-10-14) — see SOURCES.md
   "Re-verification 2026-10-14 (PASS 4 / r3-03 close-out)". All 8 returned HTTP 200;
   the two specs were content-grepped, not just status-checked:
   - RFC 9309.txt: §2.2.2 Allow/Disallow, §2.3.1.4 Unreachable, §2.3.1.5 Parsing Errors
     present; 500 KiB limit and 24 h cache confirmed.
   - WARC 1.1 spec: eight record types, mandatory fields WARC-Record-ID / WARC-Date /
     Content-Length / WARC-Payload-Digest / WARC-Target-URI confirmed; WARC-Profile
     on revisit only, WARC-Segment-* on continuation only.
   - Dedup 1.0 spec: `identical-payload-digest` profile, WARC-Refers-To-Target-URI /
     WARC-Refers-To-Date, profile URI `http://netpreserve.org/warc/0.18/revisit/identical-payload-digest`
     confirmed verbatim.
   - `https://www.iso.org/standard/82833.html` still HTTP 403 (bot-blocked, already
     recorded; the WARC 1.1 spec text is the working primary).

## What works
- RFC 9309 status-code policy is enforced in code, not prose: `robots.py --status 4xx`
  -> may crawl (§2.3.1.3); `robots.py --status 5xx` -> default-deny (§2.3.1.4). Both
  paths are exercised by `tests/test_cli_edge.py`.
- First-match robots parsing is replaced by Allow-over-Disallow precedence; the
  precedence table is in `references/crawl-policy.md`.
- WARC record hygiene: `warc_writer.py` refuses a `revisit` without `--payload-digest`
  (the empty-block-digest trap) and `--validate` re-reads its own output.
- Multi-member WARC reading: the validator walks all gzip members because
  `gzip.open()` returns only the first (verified live against the Python stdlib docs).
- Resume is byte-level: `resume_state.py` persists `{url: last_seen, offset}` and the
  queue; on restart it skips seen URLs and appends to the WARC.
- Hostile-input defense: robots.txt capped at 500 KiB, pages at 1 MiB, encodings
  decoded, nothing executed.

## What is stubbed / missing
None. All scripts run offline; all 33 tests pass; the validator finds 0 problems;
11 eval prompts with expected behaviour and failure signs are shipped.

## Acceptance verdict
**PASS.** The skill validates, scripts run offline, EVALS exist (11 prompts), the
SKILL.md body is 90 lines (<500), and every version-sensitive fact is marked with the
version and date it was verified (RFC 9309 2022, WARC 1.1 / ISO 28500:2017, dedup 1.0,
2026-10-14). No push, no history rewrite, no paths outside
`skills/agentic-data/polite-crawling-warc/**` touched this pass.
