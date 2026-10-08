# Crawl policy — polite-crawling-warc

Project defaults (override per-site in the crawl config).

| Parameter | Default | Notes |
|-----------|---------|-------|
| Crawl-delay (s) | 3.0 | from robots.txt `Crawl-delay:` if present |
| Request-rate | 0.33/s | 1 per 3 s |
| Max concurrent hosts | 1 | never parallel-host hammering |
| Retry on 429/5xx | 3 attempts | backoff 5s -> 10s -> 20s, honor Retry-After |
| robots.txt cache | 24 h | RFC 9309 §2.3.1.4 |
| robots.txt parse limit | 500 KiB | RFC 9309 §2.3.1.3 |
| User-Agent | "OttiliCrawler/1.0 (+https://ottili.example/bot)" | descriptive, contactable |
| Page size cap | 5 MiB | skip larger, log as truncated |
| Depth cap | 5 | per seed |
