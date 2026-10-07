# DESIGN: publish-reconcile-wp-meta

## Trigger description (SKILL.md description draft, <=1024 chars)
"Publish content idempotently to WordPress and Meta for Ottili flows and reconcile unknown results: create/update posts, handle API errors, and reconcile when the result is unknown. Use when an agent must publish to WordPress or Meta; when a publish call returns an unknown result; or when reconciling a failed publish. Not for general CMS logic or non-WordPress/Meta platforms."

## Procedure outline
1. **Idempotent publish** — every publish call carries a client-generated idempotency key; on a duplicate key, return the existing post id, never create a second.
2. **WordPress path** — use the WP REST API with Basic Auth or OAuth; create/update posts via the /wp/v2/posts endpoint.
3. **Meta path** — use the Meta Graph API with a page access token; create/update posts via the /{page-id}/feed endpoint.
4. **Handle errors** — map API error codes to fixes; treat 4xx as blocking (except 409 which means conflict/duplicate). Retry 5xx with exponential backoff up to 3 attempts.
5. **Reconcile unknown results** — if the response is ambiguous (timeout, partial success), re-query both APIs by idempotency key and log the delta between WP and Meta states.
6. **Log** — record every publish attempt with the idempotency key, target platform and outcome.

## Scripts planned
- `scripts/wp_publish.py` — publishes to WordPress via REST API with an idempotency key.
- `scripts/meta_publish.py` — publishes to Meta via Graph API with an idempotency key.
- `scripts/reconcile.py` — reconciles WP vs Meta state when result is unknown; emits delta report.

## Five eval prompts
1. "Publish this post to WordPress twice with the same idempotency key." -> must return the same post id both times and never create two posts.
2. "Meta returns HTTP 409 on publish." -> must treat 409 as conflict/duplicate and re-query by idempotency key rather than retry blindly.
3. "The publish call times out with no response." -> must treat as unknown result, re-query both APIs by idempotency key and log the delta.
4. "Reconcile this post between WordPress and Meta." -> must compare state on both platforms and report match/mismatch with the delta.
5. "Can we publish to any URL?" -> must use the configured WP/Meta endpoints only and reject arbitrary hosts (SSRF-safe).
