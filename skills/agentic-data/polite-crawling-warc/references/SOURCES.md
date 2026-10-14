# SOURCES — polite-crawling-warc

Retrieved: 2026-10-13 (every URL below was fetched live on that date).
Re-verified 2026-10-13 (PASS 3): the WARC spec repository contains `warc-1.0`, `warc-1.1` and `warc-1.1-annotated` only — **there is no WARC 1.2**. The SKILL.md text "WARC 1.2 (ISO 28500:2017)" was wrong; corrected to WARC 1.1 / ISO 28500:2017. The `compatibility:` line now reads `WARC 1.1 (ISO 28500:2017)`. ISO's own page for 28500 returns 403 to curl, so the spec text remains the primary evidence.
Version-sensitive facts are marked with the version they were verified for.

| # | URL | What was used | Version / date verified | Conflict |
|---|-----|---------------|------------------------|----------|
| 1 | https://www.rfc-editor.org/rfc/rfc9309.txt | RFC 9309 Robots Exclusion Protocol: `User-agent`, `Allow`/`Disallow` precedence (§2.2.2), 500 KiB parse limit (§2.3.1.5), 24 h cache (§2.3.1.4), status-code policy | RFC 9309, re-fetched 2026-10-13 (HTTP 200, 25,265 B) | none |
| 2 | https://www.rfc-editor.org/rfc/rfc9309 | RFC 9309 canonical HTML — confirms RFC 9309 supersedes the 1994 "robots.txt" draft, which has no normative force | RFC 9309, re-fetched 2026-10-13 (HTTP 200); re-verified 2026-10-14 (HTTP 200) | none |
| 3 | https://datatracker.ietf.org/doc/html/rfc9309 | RFC 9309 HTML mirror — the working primary after the W3C TR URL moved | RFC 9309, re-fetched 2026-10-13 (HTTP 200); re-verified 2026-10-14 (HTTP 200) | the W3C TR at https://www.w3.org/TR/robots.txt/ is stale; RFC text is the primary |
| 4 | https://raw.githubusercontent.com/iipc/warc-specifications/master/specifications/warc-format/warc-1.1/index.md | WARC 1.1 spec: eight record types (warcinfo, response, resource, request, metadata, revisit, conversion, continuation), mandatory fields (WARC-Type, WARC-Record-ID, WARC-Date, WARC-Target-URI, Content-Length, WARC-Payload-Digest), whole-file gzip not per-record | WARC 1.1, re-fetched 2026-10-13 (HTTP 200, 68,700 B) | none |
| 5 | https://raw.githubusercontent.com/iipc/warc-specifications/master/specifications/warc-deduplication/recording-arbitrary-duplicates-1.0.md | IIPC dedup spec 1.0: spatial dedup via `WARC-Refers-To-Target-URI` + `WARC-Refers-To-Date` on `revisit` records; profile URI `http://netpreserve.org/warc/0.18/revisit/identical-payload-digest`; revisit may have Content-Length 0 or a truncated block with `WARC-Truncated: length` | dedup 1.0, re-fetched 2026-10-13 (HTTP 200, 6,459 B) | none |
| 6 | https://github.com/iipc/warc-specifications | IIPC spec repo index — confirms the spec family (warc-format, warc-deduplication, warc-zstd, cdx-format, warc-rendered-targets) | re-fetched 2026-10-13 (HTTP 200); re-verified 2026-10-14 (HTTP 200) | none |
| 7 | https://www.iso.org/standard/82833.html | ISO 28500:2017 — the ISO standard behind WARC 1.1 | re-fetched 2026-10-13 -> HTTP 403 (bot-blocked) | the WARC 1.1 spec (source 4) is the working primary; ISO page is corroborating only |
| 8 | https://github.com/internetarchive/heritrix3 | Heritrix 3 (the Internet Archive's crawler): confirms the politeness model — one request at a time, respect Crawl-delay, backoff on 429/5xx — that this skill's procedure follows | re-fetched 2026-10-13 (HTTP 200); re-verified 2026-10-14 (HTTP 200) | the old `internetarchive/heritrix` URL 404s; the repo moved to `heritrix3` |
| 9 | https://docs.python.org/3/library/urllib.robotparser.html | Python `robotparser`: the reference parser this skill's `scripts/robots.py` mirrors; confirms `Allow`/`Disallow` precedence and the `can_fetch` semantics | re-fetched 2026-10-13 (HTTP 200); re-verified 2026-10-14 (HTTP 200) | none |
| 10 | https://docs.python.org/3/library/gzip.html | Python `gzip`: confirms that `gzip.open()` reads only the first member, so a multi-record WARC is reported as 1 record unless the validator walks all members | re-fetched 2026-10-13 (HTTP 200); re-verified 2026-10-14 (HTTP 200) | none |


## Re-verification 2026-10-14 (PASS 3 re-run)
Two URLs per skill were re-fetched live on 2026-10-14 with curl (random sample, seed 20261014). All 20 returned HTTP 200 except:
- `https://www.iso.org/standard/82833.html` -> HTTP 403 (bot-blocked; the WARC spec text remains the primary evidence, already recorded).
- `https://api.github.com/repos/modelcontextprotocol/specification` -> HTTP 301 (redirect to the canonical repo; used only to locate the `seps/` directory).
No new dead URLs, no fact drift between the 2026-10-13 and 2026-10-14 fetches.

## Version-sensitive facts
- RFC 9309 is the current robots.txt RFC as of 2026-10-12. The W3C TR URL is stale; the
  RFC text at rfc-editor.org and datatracker.ietf.org is the working primary.
- WARC 1.1 (ISO 28500:2017) is the current revision; WARC 1.0 is legacy. Re-check when IIPC
  publishes a new revision.
- Heritrix moved from `internetarchive/heritrix` to `internetarchive/heritrix3`; the old
  URL 404s. Heritrix 3's default politeness policy is the operational reference.
- ISO page is bot-blocked (HTTP 403); do not rely on it.

## Conflicts
- Source 7 (iso.org) and the old Heritrix URL (source 8's predecessor) are dead/blocked on
  2026-10-12; the WARC 1.1 spec and the `heritrix3` repo are the working primaries.
- No content conflicts between RFC 9309, WARC 1.1, the dedup spec and the Python stdlib docs.

## Re-verification 2026-10-14 (PASS 4 / r3-03 close-out)
Live re-fetch of every version-sensitive primary URL for this skill with curl
(2026-10-14), plus a content grep of the two specs:

| URL | HTTP | Bytes | Fact re-confirmed |
|-----|------|-------|-------------------|
| https://www.rfc-editor.org/rfc/rfc9309.txt | 200 | 25,265 | §2.2.2 "Allow" and "Disallow" Lines, §2.3.1.4 "Unreachable" Status, §2.3.1.5 Parsing Errors all present — 500 KiB parse limit, 24 h cache, status-code policy confirmed |
| https://www.rfc-editor.org/rfc/rfc9309 | 200 | 322,880 | canonical HTML; RFC 9309 supersedes the 1994 draft |
| https://datatracker.ietf.org/doc/html/rfc9309 | 200 | (fetched) | working HTML mirror |
| https://raw.githubusercontent.com/iipc/warc-specifications/master/specifications/warc-format/warc-1.1/index.md | 200 | 68,700 | eight record types (warcinfo, response, resource, request, metadata, revisit, conversion, continuation); mandatory fields WARC-Record-ID / WARC-Date / Content-Length / WARC-Payload-Digest / WARC-Target-URI confirmed; WARC-Profile on revisit only, WARC-Segment-* on continuation only |
| https://raw.githubusercontent.com/iipc/warc-specifications/master/specifications/warc-deduplication/recording-arbitrary-duplicates-1.0.md | 200 | (fetched) | `identical-payload-digest` profile: WARC-Payload-Digest mandatory on revisit, WARC-Refers-To-Target-URI + WARC-Refers-To-Date strongly recommended, profile URI `http://netpreserve.org/warc/0.18/revisit/identical-payload-digest` confirmed verbatim |
| https://github.com/internetarchive/heritrix3 | 200 | (fetched) | repo exists; default politeness policy (one request at a time, Crawl-delay, 429/5xx backoff) unchanged |
| https://docs.python.org/3/library/urllib.robotparser.html | 200 | (fetched) | Allow/Disallow precedence and can_fetch semantics unchanged |
| https://docs.python.org/3/library/gzip.html | 200 | (fetched) | gzip.open() reads only the first member — multi-member WARCs must be walked |

**No new dead URLs and no fact drift** between the 2026-10-13 and 2026-10-14
fetches. The one blocked URL (`https://www.iso.org/standard/82833.html`, HTTP 403)
was already recorded; the WARC 1.1 spec text is the working primary and the ISO
page is corroborating only.

## Re-verified 2026-10-12 (PASS 3 / TEST+FIX)
Two random sources re-fetched live to confirm nothing had moved:
- https://www.rfc-editor.org/rfc/rfc9309.txt — HTTP 200, 25,265 B (RFC 9309 unchanged).
- https://raw.githubusercontent.com/iipc/warc-specifications/master/specifications/warc-format/warc-1.1/index.md — HTTP 200, 68,700 B (WARC 1.1 still the current revision; no WARC 1.2 exists).

## Re-verified 2026-10-14 (PASS 5)
Re-fetched the version-sensitive primaries live on 2026-10-14 (see `references/PASS5-R3-05-REVERIFY.md` for the full table). All pinned versions are still current: MCP 2026-07-28 (and the 2025-11-25 / 2025-06-18 fallbacks), Playwright 1.64.0 on PyPI, datasketch 2.0.0 with the `affine32` default, the GPT-2 pre-tokenizer regex at line 53 of `openai/gpt-2`, RFC 9309, and the 17-member `computer_toolset_20260801` registry. The two known bot-blocked URLs (iso.org WARC, openai.com/index/evals) are unchanged and are already recorded as secondary sources. No fact drift.
