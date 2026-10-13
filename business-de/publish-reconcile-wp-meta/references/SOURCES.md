# SOURCES — publish-reconcile-wp-meta

Retrieval date: 2026-10-12. Every URL below was probed on that date;
the HTTP status is recorded per row. Version-sensitive facts are pinned in
`config/versions.json`; re-verify before relying on a fact.

| # | Source | URL | Retrieved | Verified version | Notes |
|---|---|---|---|---|---|
| 1 | Meta — Page Feed (publish + read) | https://developers.facebook.com/docs/graph-api/reference/page/posts | 2026-10-12 | **200 OK, Graph API v26.0** | Primary. Confirms `GET/POST /v26.0/{page-id}/feed`, Page access token required, `pages_manage_posts` + `pages_read_engagement` permissions, CREATE_CONTENT task, publish needs `message` or `link`, response shape `data[].id` = `{page-id}_{post-id}`. Max ~600 ranked published posts/year; `limit` capped at 100. |
| 2 | Meta — Webhooks Getting Started | https://developers.facebook.com/docs/graph-api/webhooks/getting-started | 2026-10-12 | **200 OK** | Confirms the webhook subscription model used to *observe* publish results (see `webhooks-safe`). |
| 3 | Meta — Webhooks Edge Reference | https://developers.facebook.com/docs/graph-api/webhooks | 2026-10-12 | **200 OK** | Confirms object/field subscription and the `entry[]`/`changes[]` payload shape used for reconciliation. |
| 4 | WordPress.org — REST API Handbook | https://developer.wordpress.org/rest-api/ | 2026-10-12 | **200 OK** | Confirms the WP REST API is the outbound publishing surface; authentication via Application Passwords or OAuth 2. |
| 5 | WordPress.org — Posts reference | https://developer.wordpress.org/rest-api/reference/posts/ | 2026-10-12 | **200 OK** | Confirms `/wp-json/wp/v2/posts`, the post schema (`id`, `link`, `status`, `date`, `slug`, `guid`), and the create/update/delete verbs. |
| 6 | WordPress.org — Authentication | https://developer.wordpress.org/rest-api/authentication/ | 2026-10-12 | **200 OK** | Confirms Application Passwords (Basic auth) and OAuth 2 as the two supported modes; cookies for the same-site editor. |
| 7 | WordPress.org — REST API reference (sites/comments/users) | https://developer.wordpress.org/rest-api/ | 2026-10-12 | **200 OK** | Confirms the multi-site scoping (`/wp-json/wp/v2/sites/{id}/posts`) relevant when Ottili publishes to several WP installs. |
| 8 | R3_VERIFIED_FACTS.md | ../ottili-planning/inputs/R3_VERIFIED_FACTS.md | 2026-10-06 | Meta Graph API versions "not verified in this round" | The Meta Graph API version was **not** verified on 2026-10-06; this pass pins **v26.0** (the version advertised on the Page Feed doc on 2026-10-12). Re-verify before an audit. |

## Conflicts / version-sensitive notes

- **Meta Graph API version: v26.0** (verified 2026-10-12 against the Page Feed doc). The 2026-10-06 facts file explicitly left Meta versions unverified; this is the first pin. Treat as verified-for-this-pass only.
- **WP has no native inbound webhook** (see `webhooks-safe` SOURCES, row 7). Publish *results* must be reconciled by polling the REST API or by a plugin-supplied webhook — the skill's reconciliation step covers both.
- **Unknown result is the core failure mode.** Both providers return 2xx with an id, but the post may later be rejected (Meta moderation, WP draft). The skill mandates a reconciliation pass that re-reads the post by id and records `unknown` until it is observable.
- **Idempotency key is client-generated.** The same client reference must be reused on retry; Meta and WP will either return the existing post or create a duplicate, so the skill defines the "same key = same post" rule.
