# DESIGN — publish-reconcile-wp-meta

## Trigger description (draft for SKILL.md front matter)

> Use this skill when an Ottili agent must **publish content idempotently to
> WordPress and/or Meta (Facebook/Instagram) and then reconcile the result**
> until the publish is observable. Triggers: "publish this post to WordPress",
> "post to the Facebook page", "is the post live yet?", "the publish returned
> an id but the post is not visible".

## What this skill does better than a generic agent

- **Idempotency by client reference**: every publish carries a
  `client_reference`; retries reuse it, so a second call returns the existing
  post instead of creating a duplicate.
- **Unknown-result reconciliation**: a 2xx with an id is NOT proof. The skill
  re-reads the post by id (WP `/wp-json/wp/v2/posts/{id}`, Meta
  `/{page-id}_{post-id}`) and records `unknown` until the status is
  observable. Never assumes success from the response code.
- **Provider-specific endpoints pinned from primary docs**: WP
  `/wp-json/wp/v2/posts` (Application Password / OAuth 2), Meta
  `POST /v26.0/{page-id}/feed` (Page access token, `pages_manage_posts`).
- **Dual-platform consistency check**: the same source content published to
  both WP and Meta must produce one reconciled record, not two.

## Procedure outline

1. **Normalize** the source content (title, body, media, status) into a
   canonical JSON with a client-generated `client_reference`.
2. **Publish to WP.** `POST /wp-json/wp/v2/posts` with Basic auth
   (Application Password) or OAuth 2. Capture `id` and `link`.
3. **Publish to Meta.** `POST /v26.0/{page-id}/feed` with a Page access
   token; capture `id` = `{page-id}_{post-id}`.
4. **Reconcile immediately.** Re-read each post by id. If the read returns
   the expected content → `published`. If it returns a draft/error →
   `unknown`, retry with backoff. If it 404s → `unknown`, escalate.
5. **Record** the reconciliation row (provider, client_reference, remote id,
   status, attempts, last-checked-at) in the ledger.

## Scripts planned

| Script | Purpose |
|---|---|
| `scripts/publish_post.py` | Idempotent dual-platform publish; takes canonical JSON, returns per-provider result with remote ids. |
| `scripts/reconcile_publish.py` | Re-reads posts by id and updates the ledger status; exits non-zero while any row is `unknown`. |

## Five eval prompts

1. **Retry without idempotency key.** "Publish the same post twice with a
   network blip in between." → The second call returns the **existing** post
   because `client_reference` is reused. Failure sign: two live posts.
2. **Unknown result.** "Meta returned `id: 123_456` and HTTP 200, but the
   GET on `123_456` returns an error." → Status is `unknown`, not
   `published`; retry with backoff. Failure sign: marking it published.
3. **WP auth failure.** "The Application Password was rotated." → The publish
   fails with a structured auth error; the row stays `unknown` and is
   escalated, not silently retried forever.
4. **Dual-platform mismatch.** "The post is live on WP but Meta returned an
   error." → The reconciliation row shows per-provider status; the overall
   record is `partial`. Failure sign: reporting the whole publish as succeeded.
5. **Re-read by id.** "A post was published an hour ago. How do you know it
   is still live?" → Re-read by id on demand; only a successful read with the
   expected content counts as `published`. Failure sign: trusting the original
   2xx forever.
