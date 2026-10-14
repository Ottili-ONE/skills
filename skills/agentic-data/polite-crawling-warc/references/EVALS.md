# EVALS — polite-crawling-warc

## E1 — crawl a site with robots.txt disallowing a path
Prompt: "Crawl example.com and archive it to WARC; /admin/ is disallowed."
Expected: robots.txt fetched and parsed; /admin/ paths skipped and logged;
every emitted record has WARC-Type, WARC-Record-ID, WARC-Date, WARC-Target-URI,
Content-Length, WARC-Payload-Digest.
Failure signs: /admin/ pages present in the WARC; records missing WARC-Record-ID;
no robots.txt decision recorded.

## E2 — respect Crawl-delay
Prompt: "Crawl a site whose robots.txt says Crawl-delay: 5."
Expected: measured interval between requests >= 5 s; rate never exceeds 1/5 s.
Failure signs: bursts of requests; 429s received and not backoffed.

## E3 — resume after interruption
Prompt: "The crawl was interrupted. Resume it and continue from where it stopped."
Expected: queue state + last offset loaded; already-crawled URLs skipped;
WARC opened in append mode; resume produces a still-valid WARC (validator passes).
Failure signs: duplicate records for the same URL; WARC no longer parseable;
offset state missing.

## E4 — identical re-capture emits revisit
Prompt: "Re-crawl a page that has not changed since the last harvest."
Expected: payload digest matches the prior record; a `revisit` record with
`identical-payload-digest` profile is emitted, with no block (Content-Length 0)
or a truncated block; WARC-Refers-To-Target-URI points at the original.
Failure signs: a full duplicate `response` record stored.

## E5 — hostile robots.txt
Prompt: "The robots.txt is 2 MiB of garbage."
Expected: parse limited to 500 KiB; default-deny applied; crawl does not start;
the failure is logged.
Failure signs: OOM or hang; crawl proceeds despite the parse failure.

## E6 — 429 handling
Prompt: "The site returns 429 with Retry-After: 30."
Expected: the crawler waits ~30 s (or backoff), retries up to 3 times, then skips
the URL and logs it; the WARC contains no partial/garbled record for it.
Failure signs: immediate retry storm; record written with a 429 body as a response.

## E7 — robots.txt 4xx means may crawl (not default-deny)
Prompt: "Crawl example.com; its robots.txt returns 404."
Expected: per RFC 9309 §2.3.1.3 the robots.txt is "Unavailable" and the crawler
**MAY** access any resource on the server; the crawl proceeds and the decision is
logged. `scripts/robots.py --status 404` prints `status_decision=true`.
Failure signs: the crawler refuses everything because robots.txt was missing;
no status decision recorded.

## E8 — robots.txt 5xx means MUST disallow
Prompt: "Crawl example.com; its robots.txt returns 503."
Expected: per RFC 9309 §2.3.1.4 the robots.txt is "Unreachable" and the crawler
**MUST** assume complete disallow; the crawl does not start and the failure is
logged. `scripts/robots.py --status 503` prints `status_decision=false`.
Failure signs: the crawler proceeds despite the 5xx; no default-deny applied.

## E9 — resume state survives a restart
Prompt: "Crawl was interrupted. Persist state, restart, and continue."
Expected: `scripts/resume_state.py --add <url> --offset N` persists the URL and
offset; on restart `--load` returns them; already-seen URLs are skipped; the WARC
is opened in append mode and stays valid (validator passes).
Failure signs: duplicate records after restart; state file lost; WARC unparseable.

## E10 — `robots.py --status 4xx` without `--path` or stdin
Prompt: "Run `robots.py --status 404` to check the robots.txt policy."
Expected: exits 0 with `status_decision=true` and "may crawl per RFC 9309 §2.3.1.3", without requiring `--path` or stdin. The `--status` branch runs before the file/stdin read.
Failure signs: exit 1 (default-deny) because the empty stdin was parsed as "no rules"; `--path` required error.

## E11 — `warc_writer.py --validate <missing file>`
Prompt: "Validate the WARC from the last crawl: `warc_writer.py --validate out.warc.gz`."
Expected: if the file is absent, exits 1 with `FAIL: WARC file not found` — a validation failure, not an argparse usage error (rc=2). The validator is part of the resume contract, so a broken resume must be reported as a validation failure.
Failure signs: exit 2 with an argparse error; silent success.

## Near-miss prompts (trigger precision — these should NOT fire this skill)

## N1 — a one-page fetch
Prompt: "Fetch https://example.com and extract the title."
Expected: No. That is a single HTTP GET, not a crawl. This skill is for crawling a *site* (multiple pages, robots.txt, sitemaps, rate limits, WARC archiving). A one-page fetch needs `curl` or `urllib`, not a politeness engine with token buckets and resume state.
Failure signs: running `robots.py` and `rate_limit.py` for a single URL; writing a WARC record for one page.

## N2 — server-side scraping
Prompt: "Scrape the internal API behind our app — it returns JSON."
Expected: No. This skill is for *polite web crawling* of HTML sites, respecting robots.txt and producing WARC archives. An internal JSON API is not a website — it has no robots.txt to respect and no HTML to archive. Use the API directly or an API client skill.
Failure signs: crawling an API endpoint; treating a JSON response as a page to archive.

## N3 — a site that is down
Prompt: "Crawl https://this-host-does-not-exist.invalid/ and archive it."
Expected: No. The skill's procedure says: 5xx/network error on robots.txt -> unreachable, default-deny, retry once, then skip. It does not invent content for a dead host. The correct behaviour is to record the failure in the WARC as a metadata record and move on, not to keep retrying or to fabricate pages.
Failure signs: retrying a dead host indefinitely; writing response records for a host that never responded.
