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

## Procedure

1. **Idempotent publish.** Every publish call carries a client-generated
   idempotency key. On a duplicate key, return the existing post id — never
   create a second.
2. **WordPress path.** Use the WP REST API (Application Passwords or OAuth2;
   Basic Auth is deprecated in WP 6.7+) with the `/wp/v2/posts` endpoint.
3. **Meta path.** Use the Meta Graph API with a page access token via the
   `/{page-id}/feed` endpoint.
4. **Handle errors.** Treat 4xx as blocking (except 409, which means
   conflict/duplicate). Retry 5xx with exponential backoff up to 3 attempts.
5. **Reconcile unknown results.** If the response is ambiguous (timeout,
   partial success), re-query both APIs by idempotency key and log the delta
   between WP and Meta states.
6. **Log.** Record every publish attempt with the idempotency key, target
   platform and outcome.

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
  reconciliation layer.
- **WordPress Basic Auth is deprecated** in WP 6.7+ (core); the plugin ships
  separately and is unmaintained. Prefer Application Passwords or OAuth2.
- **Meta sunsets API versions silently.** v19.0 is current but Meta does not
  announce deprecations. Pin the version in config and re-verify quarterly.
- **Never assume the first response is authoritative.** Neither API
  guarantees exactly-once delivery; re-query both platforms by the client
  idempotency key and compare state.
- **SSRF-safe.** Publish only to the configured WP/Meta endpoints; never
  publish to arbitrary hosts.

## Verification checklist

- [ ] Idempotency key present and client-generated
- [ ] Duplicate key returns the existing post id (or 409 → re-query)
- [ ] WP uses Application Passwords or OAuth2 (not deprecated Basic Auth)
- [ ] Meta uses a page access token, pinned version
- [ ] 4xx treated as blocking (except 409); 5xx retried with backoff
- [ ] Unknown results re-queried by idempotency key; delta logged
- [ ] Publish target validated against the configured endpoints

## References

- [Procedures and worked examples](references/procedures.md)
- [Standards and sources](references/SOURCES.md)
- [EVALS](references/EVALS.md)
- [Scripts](scripts/)
