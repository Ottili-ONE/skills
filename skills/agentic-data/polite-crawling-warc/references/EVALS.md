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
