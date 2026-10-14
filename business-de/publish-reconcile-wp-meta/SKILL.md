---
name: publish-reconcile-wp-meta
description: "Publish content idempotently to WordPress and Meta (Facebook/Instagram) and reconcile the result until the publish is observable. Use when an agent must post to WordPress, post to a Facebook page, check whether a post is live, or resolve a publish that returned an id but is not visible. Not for editing existing posts or for non-WordPress/Meta platforms."
license: MIT-compat
compatibility: "framework-agnostic; WP REST API, Meta Graph API v26.0; offline validation"
metadata: {}
allowed-tools: []
---

# publish-reconcile-wp-meta

## When to use this skill

Use this skill when an Ottili agent must **publish content idempotently** to
WordPress and/or Meta (Facebook/Instagram) and then **reconcile the result**
until the publish is observable. Do **not** use it for editing existing posts,
for non-WordPress/Meta platforms, or for publishing without a client
reference.

## Description

Publish to WordPress (`/wp-json/wp/v2/posts`, Application Password or OAuth 2)
and Meta (`POST /v26.0/{page-id}/feed`, Page access token) idempotently by
client reference, then re-read each post by id and record `unknown` until the
status is observable. A 2xx with an id is never treated as proof.

## Procedure

1. **Normalize** the source content (title, body, media, status) into a
   canonical JSON with a client-generated `client_reference`.
2. **Publish to WP.** `POST /wp-json/wp/v2/posts` with Basic auth
   (Application Password) or OAuth 2. Capture `id` and `link`.
3. **Publish to Meta.** `POST /v26.0/{page-id}/feed` with a Page access
   token; capture `id` = `{page-id}_{post-id}`.
4. **Reconcile immediately.** Re-read each post by id. If the read returns the
   expected content → `published`. If it returns a draft/error → `unknown`,
   retry with backoff. If it 404s → `unknown`, escalate.
5. **Record** the reconciliation row (provider, client_reference, remote id,
   status, attempts, last-checked-at) in the ledger.

## Decision tables

### Provider endpoints

| Provider | Create | Read by id | Auth |
|---|---|---|---|
| WordPress | `POST /wp-json/wp/v2/posts` | `GET /wp-json/wp/v2/posts/{id}` | Basic (Application Password) or OAuth 2 |
| Meta | `POST /v26.0/{page-id}/feed` | `GET /v26.0/{page-id}_{post-id}` | Page access token |

## Pitfalls from research

- **A 2xx with an id is not proof.** Both providers may later reject the post
  (Meta moderation, WP draft). Always re-read by id.
- **WordPress has no native inbound webhook.** Publish results must be
  reconciled by polling the REST API or by a plugin-supplied webhook.
- **Meta requires HTTPS with a valid TLS cert** (no self-signed).
- **The idempotency key is client-generated.** The same `client_reference`
  must be reused on retry; providers either return the existing post or create
  a duplicate.
- **Dual-platform mismatch is the common case.** A post live on WP but errored
  on Meta is `partial`, not `published`.

## Verification checklist

- [ ] Content normalized with a `client_reference`
- [ ] Published to each provider; remote id captured
- [ ] Each post re-read by id
- [ ] Status is `published` only when the read returns the expected content
- [ ] `unknown` rows carry attempts and last-checked-at
- [ ] Reconciliation row recorded in the ledger
- [ ] Dual-platform record is `partial` when one provider failed

## Scripts

- `publish_post.py` — see `references/DESIGN.md`
- `reconcile_publish.py` — see `references/DESIGN.md`

## References

- [Procedures and worked examples](references/procedures.md)
- [Standards and sources](references/SOURCES.md)
- [EVALS](references/EVALS.md)
- [Design](references/DESIGN.md)

## Related skills

Cross-links by name (one level deep, no circular dependency):

- **webhooks-safe** — the publish result arrives as an inbound webhook (Meta
  Graph, WordPress); this skill owns the signature verification and dedup that
  make the reconciliation loop safe.
