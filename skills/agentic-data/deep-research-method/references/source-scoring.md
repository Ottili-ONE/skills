# Source scoring — deep-research-method

Score every candidate source before reading it. Keep only >=6.

| Component | Weight | Values |
|-----------|--------|--------|
| Authority | 0-4 | official=4, major vendor=3, academic=3, media=2, blog/unknown=0-1 |
| Recency | 0-3 | <1yr=3, 1-3yr=2, 3-5yr=1, >5yr=0 (unless stable) |
| Corroboration | 0-3 | 3+ independent=3, 2=2, 1=1, none=0 |

Total = authority + recency + corroboration (max 10).

A source that scores <6 is discarded before it is read, unless it is the *only*
source for a sub-question — in which case it is kept, flagged low-confidence,
and the lack of corroboration is stated in the answer.

Version-sensitive facts (laws, API versions, vendor behaviour) get a re-fetch
note: "verified for version X on date Y; re-verify before relying on it after
any new release".
