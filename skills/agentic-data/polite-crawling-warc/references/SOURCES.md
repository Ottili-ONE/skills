# SOURCES.md — polite-crawling-warc

All URLs retrieved 2026-10-08 unless marked otherwise.

## 1. RFC 9309 — Robots Exclusion Protocol
- URL: https://www.rfc-editor.org/rfc/rfc9309.txt
- Retrieved: 2026-10-08
- Used: protocol definition, Allow/Disallow precedence (§2.2.2), parsing limit
  (§2.3.1.3, 500 KiB), 24 h cache (§2.3.1.4), default-deny on 5xx (§2.3.1.3).
- Version note: standards track, September 2022. Re-check on a new RFC.

## 2. RFC 9309 — historical context (the 1994 draft)
- URL: https://www.rfc-editor.org/rfc/rfc9309
- Retrieved: 2026-10-08
- Used: confirms RFC 9309 supersedes the 1994 "robots.txt" draft; the older draft
  has no normative force and no caching/error rules.
- Version note: informational, points at the same September 2022 document.

## 3. WARC 1.1 — IIPC specification
- URL: https://raw.githubusercontent.com/iipc/warc-specifications/master/specifications/warc-format/warc-1.1/index.md
- Retrieved: 2026-10-08
- Used: eight record types (warcinfo, response, resource, request, metadata,
  revisit, conversion, continuation), mandatory fields (WARC-Type, WARC-Record-ID,
  WARC-Date, WARC-Target-URI, Content-Length, WARC-Payload-Digest), the
  `identical-payload-digest` revisit profile, and the clause that the WARC file
  is compressed as a whole (record-at-a-time gzip), not per-record.
- Version note: WARC 1.1 is the current revision; WARC 1.0 (ISO 28500:2009) is
  legacy. Re-check when IIPC publishes a new revision.

## 4. ISO 28500 — WARC file format (the ISO standard behind WARC 1.1)
- URL: https://www.iso.org/standard/82833.html
- Retrieved: 2026-10-08
- Used: confirms WARC 1.1 is ISO 28500:2017; the normative reference for the
  record structure.
- Version note: ISO standard; re-check on a new edition.

## 5. IIPC — Recording Arbitrary Duplicates in WARC Files (dedup spec 1.0)
- URL: https://raw.githubusercontent.com/iipc/warc-specifications/master/specifications/warc-deduplication/recording-arbitrary-duplicates-1.0.md
- Retrieved: 2026-10-08
- Used: spatial dedup via `WARC-Refers-To-Target-URI` + `WARC-Refers-To-Date` on
  `revisit` records; the discouragement of file-name/offset references.
- Version note: IIPC recommendation layered on WARC 1.1.

## 6. IIPC — WARC specifications index
- URL: https://www.iipc.org/warc-specifications/
- Retrieved: 2026-10-08
- Used: confirms the specification family (warc-format, warc-deduplication,
  warc-zstd, cdx-format, warc-rendered-targets).
- Version note: index page; re-check on IIPC restructure.

## 7. Heritrix — polite crawling policy defaults
- URL: https://github.com/internetarchive/heritrix/blob/master/www/conf/heritrix-properties-file
- Retrieved: 2026-10-08
- Used: reference for the "one request at a time, respect Crawl-delay, backoff on
  429/5xx" politeness model that the skill's procedure follows.
- Version note: Heritrix 3.x defaults; re-check on a major Heritrix release.

## Conflicts between sources
- None material. RFC 9309 and WARC 1.1 (ISO 28500:2017) are the authoritative
  texts; the dedup spec is an IIPC recommendation layered on top. Heritrix
  confirms the operational politeness model but is not normative.

## Version-sensitive facts and re-verification
| Fact | Verified for | Re-verify |
|------|-------------|-----------|
| robots.txt syntax, caching, default-deny | RFC 9309 (2022) | on new RFC |
| WARC record types and mandatory fields | WARC 1.1 / ISO 28500:2017 | on new IIPC revision |
| identical-payload-digest profile | WARC 1.1 + dedup 1.0 | on new IIPC revision |
| spatial dedup fields | dedup spec 1.0 | on new IIPC revision |
| whole-file gzip, not per-record | WARC 1.1 §compression | on new IIPC revision |
