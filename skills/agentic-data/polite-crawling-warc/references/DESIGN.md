# DESIGN: polite-crawling-warc

## Trigger description (SKILL.md description draft, <=1024 chars)
"Polite web crawling with WARC output: robots.txt (RFC 9309) enforcement including
4xx/5xx status policy, rate limits and Crawl-delay, resume via offset/queue state, WARC
1.1 record hygiene, and defense against hostile inputs. Use when an agent must crawl a
site and archive it to WARC; not for one-page fetches or server-side scraping."

## Procedure outline
1. Pre-flight: confirm Python 3.10+ and gzip; decide the output path before starting —
   a WARC is append-only, never rewrite.
2. robots.txt (RFC 9309): fetch with the descriptive User-Agent; parse limit 500 KiB
   minimum, reject larger. Precedence: most specific path wins; `Allow:` can override
   `Disallow:`. **Status-code policy is the trap**: 4xx (incl. 404) = "Unavailable" ->
   MAY access (default allow); 5xx or network error = "Unreachable" -> MUST assume
   complete disallow (default-deny). Cache <=24h. `Sitemap:` lines are hints.
3. Rate limiting: read `Crawl-delay` (s) and `Request-rate` (req/s); default 1 per 3 s,
   never more than 1/s. Enforce with a token bucket; measure wall-clock interval. On
   429/5xx honor `Retry-After`, back off 5s->10s->20s, max 3 retries, then skip+log.
4. WARC 1.1 record requirements: WARC-Type, WARC-Record-ID (`urn:uuid:<uuid4>`),
   WARC-Date (ISO 8601 UTC), WARC-Target-URI, Content-Length, WARC-Payload-Digest
   (`sha256:<hex>`). Revisit records use
   `WARC-Profile: http://netpreserve.org/warc/0.18/revisit/identical-payload-digest`.
5. Deduplication: time-based (same URI+payload -> revisit, no block) and spatial (same
   payload, different URI -> revisit with WARC-Refers-To-Target-URI per IIPC dedup spec
   1.0). Never store the duplicate block.
6. Resume: persist `{url: last_seen_iso, offset: int}` plus the queue; on restart skip
   seen URLs and open the WARC in append mode.
7. Hostile-input defense: cap robots.txt parse at 500 KiB, cap memory, never stream it
   in; validate every WARC record on write and re-validate on read.

## Scripts planned
- `scripts/robots.py`, `scripts/rate_limit.py`, `scripts/resume_state.py`,
  `scripts/warc_writer.py`, `scripts/validate_warc.py`, `scripts/validate_skill.py`.

## Five eval scenarios (expanded in `references/EVALS.md`)
1. "robots.txt returned 404. Can I crawl the site?" -> Yes: 4xx = Unavailable, default
   allow. Do not default-deny on a 404.
2. "robots.txt returned 500. Can I crawl the site?" -> No: 5xx = Unreachable, default-deny;
   do not crawl, log the failure.
3. "My WARC record has no WARC-Payload-Digest. Is that valid?" -> No: response/resource/
   revisit records require it.
4. "I re-captured the same URI with the same payload. What record do I emit?" -> A
   revisit record with identical-payload-digest, no block, pointing at the prior record.
5. "The crawler restarted. How do I avoid re-fetching?" -> Load the resume state, skip
   URLs already seen, open the WARC in append mode.

## What this skill does better than a generic agent
A generic agent fetches pages and writes them out. This skill enforces the RFC 9309
4xx/5xx status policy (the most common robots.txt mistake), the Crawl-delay token bucket,
WARC 1.1 record hygiene with exact required headers, time- and spatial-dedup via the
IIPC revisit profile, and resume state. It prevents the common incident of a crawler
that refuses to crawl a site whose robots.txt 404'd, or writes WARC records that fail
validation because they lack WARC-Payload-Digest.
