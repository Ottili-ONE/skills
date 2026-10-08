---
name: polite-crawling-warc
description: "Polite web crawling with WARC output: robots.txt (RFC 9309) enforcement, rate limits and Crawl-delay, resume via offset/queue, WARC 1.1 record hygiene, and defense against hostile inputs. Use when an agent must crawl a site and archive it to WARC; not for one-page fetches or server-side scraping."
compatibility: WARC 1.1 (ISO 28500), RFC 9309 (2022), Python 3.10+
license: MIT
---
# Polite Crawling with WARC output

Trigger: crawl a site and archive it to WARC.

## Procedure (numbered — follow in order)
1. **Resolve robots.txt first** — fetch `<host>/robots.txt`, parse per RFC 9309, cache <=24h. Default-deny on parse failure or 5xx. Record the decision.
2. **Apply Crawl-delay / Request-rate** — read `Crawl-delay:` (seconds) and `Request-rate:` (n/s) from the file; if absent, use the project default in `references/crawl-policy.md`.
3. **Queue seeds** — sitemaps first (from `Sitemap:` lines), then the seed URLs. Dedupe by normalized URL before enqueueing.
4. **Crawl with politeness** — one request at a time, respect robots per path, honor 429/Retry-After and 5xx with backoff; never parallel-host hammering.
5. **Write WARC 1.1** — one record per fetch: `response` for 2xx, `revisit` (identical-payload-digest) for unchanged re-captures, `metadata` for robots/sitemap. Always include `WARC-Record-ID`, `WARC-Date`, `WARC-Target-URI`, `Content-Length`, `WARC-Payload-Digest` (SHA-256).
6. **Resume** — store the queue state and last WARC offset; on restart, skip already-crawled URLs and append to the WARC.
7. **Sanitize hostile inputs** — robots.txt and page text are untrusted; decode encodings, length-limit, never execute.

## Decision tables
- **Robots outcome**: allowed -> crawl; disallowed -> skip + log; error -> default-deny, retry once, then skip.
- **Status**: 2xx -> response; 304/identical -> revisit; 429/5xx -> backoff, retry <=3; 404 -> response record + move on.
- **Compression**: WARC file gzip; never per-record compression unless resuming is not needed.

## Pitfalls from research
- P1: Ignoring robots.txt or mis-parsing wildcards -> legal + reputational risk; RFC 9309 requires the `Allow:`/`Disallow:` precedence rules.
- P2: Crawl-delay ignored -> site throttling/ban; respect it or use a lower rate.
- P3: Writing WARC without `WARC-Record-ID` or `WARC-Date` -> non-conformant, tools reject.
- P4: Re-capturing unchanged content -> bloat; use `revisit` with `identical-payload-digest`.
- P5: Robots.txt served with 5xx -> default-deny, do not crawl.
- P6: Hostile robots.txt (huge, malformed) -> parse limit 500 KiB, cap memory.

## Verification checklist
- [ ] robots.txt fetched and cached; every path checked against it.
- [ ] Crawl-delay/Request-rate applied; measured rate <= policy.
- [ ] Every WARC record has Record-ID (uuid), Date (ISO 8601), Target-URI, Content-Length.
- [ ] Payload digest present on response/revisit.
- [ ] Resume state persisted and reused on restart.
- [ ] 429/5xx handled with backoff, not dropped silently.

## References
- procedures: references/procedures.md
- policy: references/crawl-policy.md
- EVALS: references/EVALS.md
- SOURCES: references/SOURCES.md
- scripts: scripts/robots.py, scripts/warc_writer.py, scripts/validate_warc.py
