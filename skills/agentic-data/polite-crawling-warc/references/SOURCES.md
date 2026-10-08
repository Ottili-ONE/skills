# SOURCES.md — polite-crawling-warc

All URLs retrieved 2026-10-08 unless marked otherwise.

## 1. RFC 9309 — Robots Exclusion Protocol
- URL: https://www.rfc-editor.org/rfc/rfc9309.txt
- Retrieved: 2026-10-08
- Used: protocol definition, Allow/Disallow precedence (§2.2.2), parsing limit
  (§2.3.1.3, 500 KiB), 24 h cache (§2.3.1.4), default-deny on 5xx (§2.3.1.3).
- Version note: standards track, September 2022. Stable; re-check only on a new
  RFC. The older robots.txt "standard" (RFC 9309 supersedes the 1994 draft) is the
  authoritative text.

## 2. WARC 1.1 — ISO 28500 / IIPC specification
- URL: https://raw.githubusercontent.com/iipc/warc-specifications/master/specifications/warc-format/warc-1.1/index.md
- Retrieved: 2026-10-08
- Used: eight record types (warcinfo, response, resource, request, metadata,
  revisit, conversion, continuation), mandatory fields (WARC-Type, WARC-Record-ID,
  WARC-Date, WARC-Target-URI, Content-Length, WARC-Payload-Digest), the
  `identical-payload-digest` revisit profile, segmentation/continuation, no
  internal compression (record-at-time gzip only).
- Version note: WARC 1.1 is the current revision; WARC 1.0 (ISO 28500:2009) is
  legacy. Re-check when IIPC publishes a new revision.

## 3. IIPC — Recording Arbitrary Duplicates in WARC Files (dedup spec 1.0)
- URL: https://raw.githubusercontent.com/iipc/warc-specifications/master/specifications/warc-deduplication/recording-arbitrary-duplicates-1.0.md
- Retrieved: 2026-10-08
- Used: spatial dedup via `WARC-Refers-To-Target-URI` + `WARC-Refers-To-Date` on
  `revisit` records; the discouragement of file-name/offset references.

## 4. IIPC WARC specifications index
- URL: https://www.iipc.org/warc-specifications/
- Retrieved: 2026-10-08
- Used: confirms the specification family (warc-format, warc-deduplication,
  warc-zstd, cdx-format, warc-rendered-targets).

## 5. WARC 1.1 — file compression
- URL: (same index.md as #2, clause on compression)
- Retrieved: 2026-10-08
- Used: whole-file gzip is the demonstrated approach; per-record compression
  breaks resumability, so we compress the whole file.

## Conflicts between sources
- None material. RFC 9309 and WARC 1.1 are the authoritative texts; the dedup
  spec is an IIPC recommendation layered on top of WARC 1.1.

## Version-sensitive facts and re-verification
| Fact | Verified for | Re-verify |
|------|-------------|-----------|
| robots.txt syntax and caching | RFC 9309 (2022) | on new RFC |
| WARC record types and mandatory fields | WARC 1.1 | on new IIPC revision |
| identical-payload-digest profile | WARC 1.1 + dedup 1.0 | on new IIPC revision |
| spatial dedup fields | dedup spec 1.0 | on new IIPC revision |
