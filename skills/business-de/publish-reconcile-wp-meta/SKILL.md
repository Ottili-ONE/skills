---
name: publish-reconcile-wp-meta
description: "Publish content idempotently to WordPress and Meta for Ottili flows and reconcile unknown results: create/update posts, handle API errors, and reconcile when the result is unknown. Use when an agent must publish to WordPress or Meta; when a publish call returns an unknown result; or when reconciling a failed publish. Not for general CMS logic or non-WordPress/Meta platforms."
license: MIT-compat
compatibility: "framework-agnostic; WP REST API and Meta Graph API; offline validation"
metadata: {}
allowed-tools: []
---

# publish-reconcile-wp-meta

## When to use this skill

Use this skill when an agent must publish content to WordPress or Meta for
Ottili flows: create or update a post, handle API errors, and reconcile when
the result is unknown. Do **not** use it for general CMS logic, non-WordPress
platforms, or non-Meta social platforms.

## Procedure (numbered, in order)

1. **Check the idempotency store first.** Before every publish, look up the
   client-generated key in the store. If it exists, return the stored post
   id — never create a second post.
2. **Publish to the platform.** WordPress via `/wp/v2/posts` (Application
   Passwords or OAuth2; Basic Auth is deprecated in WP 6.7+). Meta via
   `/{page-id}/feed` on the pinned Graph API version.
3. **Store the mapping.** On success, append the key → post id mapping to the
   append-only store. Never mutate an entry in place.
4. **Handle errors.** Treat 4xx as blocking (except 409, which means
   conflict/duplicate → re-query by key). Retry 5xx with exponential backoff
   up to 3 attempts (base 500 ms, factor 2, cap 30 s).
5. **Reconcile unknown results.** If the response is ambiguous (timeout,
   partial success), re-query both APIs by idempotency key, compare state,
   log the delta. Persistent mismatch → flag for human review, never silently
   overwrite.
6. **SSRF-safe delivery.** Publish only to the configured WP/Meta endpoints;
   never publish to arbitrary hosts.

## Decision tables

### Error → fix

| HTTP status | Meaning | Fix |
|---|---|---|
| 400 | Validation error | Fix the named field |
| 401 / 403 | Auth | Re-issue credentials; never retry with the same token |
| 409 | Conflict / duplicate | Re-query by idempotency key; never re-create |
| 429 | Rate limited | Exponential backoff, up to 3 attempts |
| 5xx | Platform outage | Backoff; mark the post unknown |

### Reconcile outcome

| Situation | Action |
|---|---|
| Both platforms match | Ok; log |
| One platform newer | Re-query the older; log the delta |
| Unknown result (timeout) | Re-query both by idempotency key; log the delta |
| Persistent mismatch | Flag for human review; never silently overwrite |

## Pitfalls from research

- **POST is not idempotent by HTTP semantics.** Idempotency must be enforced
  server-side via a client-provided key. Neither WP nor Meta natively
  supports idempotency keys — the skill must implement it in the
  reconciliation layer (the `idempotency_store.py` helper).
- **WordPress Basic Auth is deprecated** in WP 6.7+ (core); the plugin ships
  separately and is unmaintained. Prefer Application Passwords or OAuth2.
- **Meta sunsets API versions silently.** v19.0 is pinned but v20.0 and v21.0
  are already listed in the changelog (re-verified 2026-10-09) — do not assume
  v19.0 is the newest. Re-verify quarterly.
- **Never assume the first response is authoritative.** Neither API
  guarantees exactly-once delivery; re-query both platforms by the client
  idempotency key and compare state.
- **SSRF-safe.** Publish only to the configured WP/Meta endpoints; never
  publish to arbitrary hosts.

## Verification checklist

- [ ] Idempotency key looked up in the store before every publish
- [ ] Duplicate key returns the existing post id (or 409 → re-query)
- [ ] WP uses Application Passwords or OAuth2 (not deprecated Basic Auth)
- [ ] Meta uses a page access token, pinned version
- [ ] 4xx treated as blocking (except 409); 5xx retried with backoff
- [ ] Unknown results re-queried by idempotency key; delta logged
- [ ] Publish target validated against the configured endpoints
- [ ] Idempotency store is append-only; no in-place mutation

## Near-miss triggers (stop and re-read)

- "I'll just POST again" → check the idempotency store first.
- "Basic Auth is fine, it's just a plugin" → deprecated in WP 6.7+ core.
- "v19.0 is the current Meta version" → v20.0 and v21.0 already exist.
- "The first response is authoritative" → re-query both platforms.

## References

- [Procedures and worked examples](references/procedures.md)
- [Standards and sources](references/SOURCES.md)
- [EVALS](references/EVALS.md)
- [Scripts](scripts/)
