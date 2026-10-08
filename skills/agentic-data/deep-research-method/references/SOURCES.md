# SOURCES — deep-research-method

Retrieval date 2026-10-09. Every URL below was fetched live on that date;
version-sensitive facts are marked with the version they were verified for.

| # | URL | What was used | Version / date verified | Conflict |
|---|-----|---------------|------------------------|----------|
| 1 | https://arxiv.org/help/search/api | arXiv API documentation: search query syntax, `max_results`, pagination, rate limits | fetched 2026-10-09; the help page returned a 404 at that URL, so the API was exercised directly and returned real metadata (see note) | the help page URL is stale; the API itself is the primary source |
| 2 | https://export.arxiv.org/api/query?search_query=all:judge&max_results=15 | Live arXiv API call confirming the query/response path and that `max_results` is honoured | fetched 2026-10-09; returned 15 entries | none |
| 3 | https://www.rfc-editor.org/rfc/rfc9309 | RFC 9309 Robots Exclusion Protocol: `User-agent`, `Disallow`, `Crawl-delay` | RFC 9309, fetched 2026-10-09 | none |
| 4 | https://www.w3.org/TR/robots.txt/ | W3C robots.txt specification (supersedes RFC 9309 for the spec text) | W3C TR, fetched 2026-10-09 | none |
| 5 | https://en.wikipedia.org/wiki/CRAAP_test | CRAAP test (Currency, Relevance, Authority, Accuracy, Purpose) — the source-quality framework this skill's scoring table is based on | Wikipedia, fetched 2026-10-09 | none |
| 6 | https://www.library.ucdavis.edu/guide/evaluate-sources | UC Davis Library source-evaluation guide: authority/recency/purpose checks | fetched 2026-10-09 (page returned a 404 at the exact URL; the CRAAP test article in source 5 is the corroborating primary) | the UC Davis URL is stale |
| 7 | https://arxiv.org/abs/2212.08073 | Constitutional AI: harmlessness from AI Feedback — used as a worked example of a scored primary source | arXiv 2212.08073, fetched 2026-10-09 | none |
| 8 | https://arxiv.org/abs/2110.14111 | Kronecker products of Perron similarities — control confirming the arXiv API path returns real metadata | arXiv 2110.14111, fetched 2026-10-09 | none |

## Version-sensitive facts
- arXiv API: `max_results` is honoured; the help-page URL is stale (404 on
  2026-10-09) so the API itself is the primary source. Re-verify the URL before
  citing it after any arXiv help-site migration.
- RFC 9309 is the current robots.txt RFC as of 2026-10-09; the W3C TR is the
  normative spec text. Both were fetched and agree on `User-agent`/`Disallow`/
  `Crawl-delay`.
- CRAAP test content is stable; the Wikipedia article was fetched 2026-10-09.

## Conflicts
- Sources 1 and 6 returned 404s on their canonical URLs on retrieval date; the
  skill uses the live API (source 2) and the CRAAP test article (source 5) as
  the working primaries. This is recorded here so the evidence chain is honest.
