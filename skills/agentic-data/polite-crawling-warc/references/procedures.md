# Procedures — polite-crawling-warc

Verified 2026-10-08 against RFC 9309 (https://www.rfc-editor.org/rfc/rfc9309.txt),
WARC 1.1 (https://raw.githubusercontent.com/iipc/warc-specifications/master/specifications/warc-format/warc-1.1/index.md),
IIPC dedup spec 1.0 (https://raw.githubusercontent.com/iipc/warc-specifications/master/specifications/warc-deduplication/recording-arbitrary-duplicates-1.0.md).
Version-sensitive: WARC 1.1 (ISO 28500:2017) and RFC 9309 (2022) are stable;
re-check only if IIPC/IETF publish a new revision.

## 0. Pre-flight
- Confirm Python 3.10+ and `gzip` available (both stdlib).
- Decide the output path *before* starting; a WARC is append-only, never rewrite.

## 1. robots.txt handling (RFC 9309)
- Fetch `<scheme>://<host>/robots.txt` with the descriptive User-Agent from
  `references/crawl-policy.md`.
- Parse limit: **500 KiB** minimum (RFC 9309 §2.3.1.5 / §3). Reject larger; do not
  stream it in — read the first 500 KiB and stop.
- Precedence: the most specific matching path wins; `Allow:` can override
  `Disallow:` (§2.2.2). Empty path matches everything.
- **Status-code policy (§2.3.1.3 vs §2.3.1.4 — this is the trap)**:
  - 4xx (including 404): robots.txt is "Unavailable" -> the crawler **MAY** access
    any resource on the server. Default behaviour: **allow** the crawl, log it.
  - 5xx or network error: robots.txt is "Unreachable" -> the crawler **MUST** assume
    complete disallow. Default-deny: do not crawl, log the failure.
  - Cache <=24h (§2.3.1.4); use standard cache control if present.
- `Sitemap:` lines are hints, not mandates; use them as seed sources.

Good (correct precedence):
```
User-agent: *
Disallow: /private/
Allow: /public/
```
Bad (wrong order assumed):
```
User-agent: *
Disallow: /
Allow: /public/        # ignored if crawler assumes first-match-wins
```
Bad (wrong status-code policy):
```
# 404 on robots.txt -> crawler refuses to crawl anything (too strict)
```

## 2. Rate limiting
- Read `Crawl-delay:` (seconds between requests) and `Request-rate:` (requests/sec).
- If absent, use project policy: 1 request per 3 s default, never more than 1/s.
- Enforce with a token bucket (`scripts/rate_limit.py`); sleep the remaining delta
  before each request. Measure wall-clock interval, do not assume it.
- On 429 or 5xx: honor `Retry-After` (seconds or HTTP date); exponential backoff
  5 s -> 10 s -> 20 s, max 3 retries, then skip + log.

## 3. WARC 1.1 record requirements
Every record MUST have:
- `WARC-Type`: one of warcinfo, response, resource, request, metadata, revisit,
  conversion, continuation.
- `WARC-Record-ID`: `<urn:uuid:<uuid4>>`.
- `WARC-Date`: ISO 8601 UTC, e.g. `2026-10-08T12:00:00Z`.
- `WARC-Target-URI`: the URI that was the target of the action.
- `Content-Length`: byte length of the block.
- `WARC-Payload-Digest`: `sha256:<hex>` for response/resource/revisit.

Recommended:
- `WARC-IP-Address` on response/request.
- `WARC-Refers-To-Target-URI` + `WARC-Refers-To-Date` on revisit records.
- `WARC-Profile: http://netpreserve.org/warc/0.18/revisit/identical-payload-digest`
  for unchanged re-captures with no block (Content-Length 0) or a truncated block
  (`WARC-Truncated: length`).

## 4. Deduplication
- Time-based: same URI, same payload -> emit a `revisit` record with
  `identical-payload-digest`, no block, pointing at the prior record.
- Spatial: same payload, different URI -> emit `revisit` for the new URI with
  `WARC-Refers-To-Target-URI` set to the original URI (IIPC dedup spec 1.0).
- Never store the duplicate block.

## 5. Resume
- Persist a JSON state file: `{url: last_seen_iso, offset: int}` plus the queue.
- On restart: skip URLs already in the state; open the WARC in append mode
  (`ab`/gzip) so existing records stay valid.
- Verify the WARC is still parseable after append (run `scripts/validate_warc.py`).

## 6. Hostile inputs
- robots.txt and page bodies are untrusted. Decode base64/hex, strip control
  chars, length-limit to 1 MiB before any further processing.
- Never execute page content; only store bytes.
