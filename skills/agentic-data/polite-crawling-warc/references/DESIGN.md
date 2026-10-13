# DESIGN: polite-crawling-warc

## Rationale (why this skill exists)
A one-off `curl` call does not care about robots.txt, rate limits or archives.
When the job is to crawl a site and keep a WARC, every one of those concerns
becomes a hard requirement: a crawler that ignores `Crawl-delay` gets the site
blacklisted; a crawler that rewrites its WARC loses the archive; a crawler that
streams an unbounded robots.txt is open to a memory-exhaustion attack. This skill
exists to make the polite-and-persistent combination the default rather than the
exception.

## Trigger description (SKILL.md description draft, <=1024 chars)
"Polite web crawling with WARC output: robots.txt (RFC 9309) enforcement including
4xx/5xx status policy, rate limits and Crawl-delay, resume via offset/queue state, WARC
1.1 record hygiene, and defense against hostile inputs. Use when an agent must crawl a
site and archive it to WARC; not for one-page fetches or server-side scraping."

## The three hard decisions (and why they are hard)

### 1. Status-code policy is the trap
RFC 9309 §2.3.1.3 splits the world into "Unavailable" (4xx, including 404) and
"Unreachable" (5xx or network error). The trap is that these map to *opposite*
default rules: a 404 on the robots.txt means MAY crawl (default allow), while a 5xx
means MUST assume complete disallow (default-deny). A crawler that treats both as
"skip" will fail to crawl sites whose robots.txt 404s; a crawler that treats both
as "allow" will crawl sites that are unreachable and therefore likely to be
misconfigured or overloaded. The rule is: **fetch the status code, branch on it,
never guess.**

### 2. WARC is append-only
A WARC is a concatenation of records with no trailer. Rewriting it means rewriting
every record. So the design decision is made *before* the first byte is written:
decide the output path, open in append mode, and never reopen for edit. Resume
state (`{url, last_seen_iso, offset}`) is persisted alongside, not inside, the
WARC.

### 3. robots.txt precedence
`Allow:` can override `Disallow:` on a more specific path. The most-specific match
wins, and within a match the first rule wins — but an `Allow:` whose path is longer
than the corresponding `Disallow:` takes precedence even if it appears later. This
is the IETF's explicit tie-break and it is the opposite of what a naive
first-match parser does.

## Scripts shipped (what each one does, not just its name)
- `scripts/robots.py` — fetch, parse (500 KiB cap) and apply RFC 9309 with the
  status-code policy and Allow-over-Disallow precedence.
- `scripts/rate_limit.py` — token-bucket pacing from `Crawl-delay` / `Request-rate`,
  honoring `Retry-After` with 5s/10s/20s backoff, 3 retries, then skip+log.
- `scripts/resume_state.py` — persist and reload `{url, last_seen_iso, offset}` so a
  killed crawl restarts where it stopped.
- `scripts/warc_writer.py` — append WARC 1.1 records with mandatory fields and
  payload digests; `--validate` re-reads its own output.
- `scripts/validate_warc.py` — structural validation of a WARC file (record types,
  mandatory fields, digest checks).
- `scripts/validate_skill.py` — standard compliance for the skill itself.

## Near-miss triggers
- Treating a 4xx robots.txt as a block -> sites whose robots.txt 404s are never crawled.
- Treating a 5xx robots.txt as "may crawl" -> hammer an already-failing site.
- Rewriting the WARC in place -> archive corruption; decide the path first.
- Streaming an unbounded robots.txt -> memory-exhaustion attack; cap at 500 KiB.
- First-match robots parsing -> Allow-over-Disallow precedence is silently lost.
- Resuming without the offset -> records are re-appended and the archive is duped.
