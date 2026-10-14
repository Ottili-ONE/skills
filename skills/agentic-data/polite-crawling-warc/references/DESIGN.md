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

## What this skill does better than a generic agent
A generic agent writes a `for url in urls: requests.get(url)` loop and calls it a
crawler. This skill makes the crawl auditable, resumable and legally defensible.

- **robots.txt is a decision, not a checkbox**: the skill distinguishes 2xx
  (obey), 4xx (may crawl, RFC 9309 §2.3.1.3) and 5xx (default-deny, §2.3.1.4).
  A generic agent that treats a 404 as "no robots" and a 503 as "no robots"
  gets the two cases backwards.
- **WARC is a contract, not a file format**: every record carries
  `WARC-Record-ID`, `WARC-Date`, `WARC-Target-URI`, `Content-Length` and
  `WARC-Payload-Digest`, and the validator walks every gzip member rather than
  reading the first (verified live 2026-10-08: a 3-record file reads as 1
  record otherwise).
- **Resume is a first-class feature**: queue + offset state is persisted
  atomically (write `.tmp`, rename), so an interrupted crawl resumes without
  duplicating records or corrupting the WARC.
- **Hostile inputs are bounded before they are parsed**: robots.txt capped at
  500 KiB, pages at 1 MiB, encodings decoded, nothing executed.

## What existing public skills do (and what this one does differently)

Surveyed on 2026-10-12. `anthropics/skills`, the Fastio 2026 directory and
`skills.cat` carry no crawling/WARC skill. The topic lives in the
`webrecorder/pywb` and `internetarchive/heritrix3` ecosystems and in RFC 9309,
not in agent skill form. Community crawlers are either a single `requests`
loop with no robots handling, or a full Heritrix deployment that an agent
cannot configure from a prompt.

This skill is the first crawler that an agent can run from a prompt and that
produces a standards-conformant, resumable archive:
- **RFC 9309 status policy is explicit and version-pinned**: the 4xx/5xx
  distinction is the part most implementations get wrong, and it is the
  difference between "may crawl" and "must not crawl".
- **WARC 1.1 record hygiene is checkable**: `scripts/warc_writer.py --validate`
  re-reads its own output and exits 1 on any missing field, so a broken
  archive fails the resume contract instead of being silently archived.
- **Rate limiting is measured, not hoped for**: the token-bucket enforces the
  measured interval between requests, and the eval verifies it against a
  `Crawl-delay: 5` policy.
- **Everything is offline-deterministic**: no API keys, no cloud storage, no
  remote fetches during validation.

Public sources surveyed (2026-10-12, all HTTP 200):
| Source | What it has | Gap this skill fills |
|--------|-------------|---------------------|
| RFC 9309 (2022) | the robots.txt spec | a spec, not a crawler; no WARC, no resume |
| `webrecorder/pywb` | WARC tooling | a library; needs a crawler around it |
| `internetarchive/heritrix3` | a full crawler | a deployment, not a script an agent runs |

## Five eval scenarios (expanded in `references/EVALS.md`)
1. "Crawl example.com; /admin/ is disallowed." -> robots.txt fetched and parsed; /admin/ paths skipped and logged; every record has WARC-Type, WARC-Record-ID, WARC-Date, WARC-Target-URI, Content-Length, WARC-Payload-Digest.
2. "The site says Crawl-delay: 5." -> measured interval between requests >= 5 s; rate never exceeds 1/5 s; 429s backoff with 5s/10s/20s, max 3 retries.
3. "The crawl was interrupted. Resume it." -> queue state + last offset loaded; already-crawled URLs skipped; WARC opened in append mode; resume produces a still-valid WARC (validator passes).
4. "Re-crawl a page that has not changed." -> payload digest matches the prior record; a `revisit` record with `identical-payload-digest` is emitted, not a full duplicate `response`.
5. "robots.txt returns 404 / 503." -> 404 -> may crawl (§2.3.1.3), exit 0; 503 -> default-deny (§2.3.1.4), exit 1. The script runs `--status` before reading the file, so a missing path does not silently flip the answer.

## Procedure outline
1. **Resolve robots.txt first** — fetch `<host>/robots.txt`, parse per RFC 9309, cache <=24h. 4xx -> may crawl; 5xx/network error -> default-deny. Record the decision.
2. **Apply Crawl-delay / Request-rate** — read `Crawl-delay:` (seconds) and `Request-rate:` (n/s); if absent, use the project default in `references/crawl-policy.md`. Enforce with a token bucket (`scripts/rate_limit.py`).
3. **Queue seeds** — sitemaps first (from `Sitemap:` lines), then the seed URLs. Dedupe by normalized URL before enqueueing.
4. **Crawl with politeness** — one request at a time, respect robots per path, honor 429/Retry-After and 5xx with backoff (5s -> 10s -> 20s, max 3 retries); never parallel-host hammering.
5. **Write WARC 1.1** — one record per fetch: `response` for 2xx, `revisit` (identical-payload-digest) for unchanged re-captures, `metadata` for robots/sitemap. Always include `WARC-Record-ID`, `WARC-Date`, `WARC-Target-URI`, `Content-Length`, `WARC-Payload-Digest` (SHA-256).
6. **Resume** — persist queue + `{url: last_seen, offset}` via `scripts/resume_state.py`; on restart, skip seen URLs and append to the WARC. Validate the WARC after append with `scripts/warc_writer.py --validate`.
7. **Sanitize hostile inputs** — robots.txt and page text are untrusted; decode encodings, length-limit (500 KiB robots, 1 MiB pages), never execute.

## Scripts shipped (what each one does, not just its name)
- `scripts/robots.py` — fetch and parse robots.txt per RFC 9309; `--status` runs before the file/stdin read so a 4xx/5xx decision cannot be flipped by a missing path.
- `scripts/rate_limit.py` — token-bucket enforcing Crawl-delay / Request-rate; measured interval between requests is the check, not a sleep.
- `scripts/resume_state.py` — persist queue + offset atomically (write `.tmp`, rename); skip seen URLs on restart.
- `scripts/warc_writer.py` — emit WARC 1.1 records; `--validate` re-reads its own output and walks every gzip member.
- `scripts/validate_warc.py` — independent WARC 1.1 conformance check.
- `scripts/validate_skill.py` — standard-rules check reused by the other skills.
