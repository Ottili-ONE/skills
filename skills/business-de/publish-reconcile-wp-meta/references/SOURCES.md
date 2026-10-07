# SOURCES: publish-reconcile-wp-meta
Retrieval date: 2026-10-07. All URLs fetched with `curl` on 2026-10-07 unless noted otherwise. Version-sensitive facts pinned in config; never hardcoded in logic (R3 rule). Re-verify before each release.

## Versions verified
- WordPress REST API v2 — WP 6.7+ stable as of 2026-10-07; endpoint contract stable since WP 5.0. Re-verify against https://developer.wordpress.org/rest-api/ before each build.
- Meta Graph API v19.0+ — current as of 2026-10-07; page access tokens, /{page-id}/feed endpoint. Re-verify against https://developers.facebook.com/docs/graph-api before each build.

## Primary sources
1. WordPress REST API reference — https://developer.wordpress.org/rest-api/reference/ — retrieved 2026-10-07. Authorisation, post create/update endpoints, error codes.
2. Meta for Developers: Graph API — https://developers.facebook.com/docs/graph-api — retrieved 2026-10-07. Page feed, error codes, rate limiting.
3. WordPress REST API handbook: authentication — https://developer.wordpress.org/rest-api/authentication/ — retrieved 2026-10-07. Basic Auth (deprecated in WP 6.7+), OAuth, Application Passwords.
4. Meta for Developers: rate limiting — https://developers.facebook.com/docs/graph-api/rate-limiting — retrieved 2026-10-07. Error codes 429, 17, exponential backoff guidance.
5. Idempotency patterns in REST — https://www.rfc-editor.org/rfc/rfc9110 — retrieved 2026-10-07. HTTP semantics for idempotency (PUT/DELETE vs POST).
6. OWASP API Security Top 10 — https://owasp.org/www-project-api-security/ — retrieved 2026-10-07. SSRF guidance, token handling, replay protection.
7. WordPress: Application Passwords — https://wordpress.org/support/article/application-passwords/ — retrieved 2026-10-07. Secure credential pattern for plugins/scripts.
8. Meta: Page access tokens — https://developers.facebook.com/docs/pages/overview — retrieved 2026-10-07. Token lifecycle, expiry, refresh patterns.

## Conflicts / open questions
- WordPress Basic Auth plugin is deprecated in WP 6.7+ (core); the plugin ships separately and is unmaintained. Treat Basic Auth as legacy; prefer Application Passwords or OAuth2. Pin the WP version and re-verify.
- Meta Graph API versioning: v19.0 is current but Meta sunsets versions silently; pin the version in config and re-verify quarterly.
- Idempotency: POST is not idempotent by HTTP semantics; idempotency must be enforced server-side via a client-provided key. Both WP and Meta lack native idempotency keys — the skill must implement it in the reconciliation layer.
- Unknown-result reconciliation: neither API guarantees exactly-once delivery; the skill must re-query both platforms by the client idempotency key and compare state, never assume the first response is authoritative.
