# Procedures — publish-reconcile-wp-meta

All endpoints, credentials and versions are read from `config/versions.json`
(never hardcode). Re-verify each provider's API contract before every build
and record the retrieval date in `references/SOURCES.md`.

## 1. Idempotent publish

Every publish call carries a client-generated idempotency key. The key is
your own content reference; it must be stable across retries. On a duplicate
key the platform returns the existing post id — never create a second.

**POST is not idempotent by HTTP semantics.** Neither WP nor Meta natively
supports idempotency keys, so the skill implements idempotency in the
reconciliation layer: store the key → post id mapping, and on a duplicate
key return the stored post id.

## 2. WordPress path

- Endpoint: `https://<site>/wp/v2/posts`
- Auth: Application Passwords or OAuth2. **Basic Auth is deprecated in WP
  6.7+** (core); the plugin ships separately and is unmaintained. Prefer
  Application Passwords.
- Create: `POST /wp/v2/posts` with `title`, `content`, `status`.
- Update: `POST /wp/v2/posts/<id>` (same body).
- The idempotency key is stored as a custom field or meta field for
  re-query.

```bash
curl -s -X POST "$WP_URL/wp/v2/posts" \
  -u "user:$APP_PASSWORD" \
  -H 'Content-Type: application/json' \
  -d @post.json
```

**Good output** (first call):
```json
{"id": 42, "link": "https://example.com/?p=42", "status": "publish"}
```
**Bad output** — two posts created for one content reference:
```json
[{"id": 42, "link": "..."}, {"id": 43, "link": "..."}]
```
Detect it: two distinct `id` values for the same idempotency key.

## 3. Meta path

- Endpoint: `https://graph.facebook.com/v19.0/{page-id}/feed`
- Auth: page access token in the `access_token` query parameter or header.
- Create: `POST /{page-id}/feed` with `message`, `published`.
- Update: `POST /{post-id}` (same body).
- Meta sunsets API versions silently; pin the version in config and
  re-verify quarterly.

```bash
curl -s -X POST "https://graph.facebook.com/v19.0/123456789/feed" \
  -d "access_token=$PAGE_TOKEN" \
  -d "message=Hello"
```

## 4. Error → fix

| HTTP status | Meaning | Fix |
|---|---|---|
| 400 | Validation error | Fix the named field |
| 401 / 403 | Auth failure | Re-issue credentials; never retry with the same token |
| 409 | Conflict / duplicate | Re-query by idempotency key; never re-create |
| 429 | Rate limited | Exponential backoff, up to 3 attempts |
| 5xx | Platform outage | Backoff; mark the post unknown |

## 5. Reconcile unknown results

If the response is ambiguous (timeout, partial success), re-query both APIs
by idempotency key and log the delta between WP and Meta states.

| Situation | Action |
|---|---|
| Both platforms match | Ok; log |
| One platform newer | Re-query the older; log the delta |
| Unknown result (timeout) | Re-query both by idempotency key; log the delta |
| Persistent mismatch | Flag for human review; never silently overwrite |

## 6. SSRF-safe delivery

Publish only to the configured WP/Meta endpoints. Never publish to arbitrary
hosts — an attacker-controlled content field that triggers a publish to an
arbitrary host is an SSRF. Validate the target against the allow-list.

## 7. Offline helper scripts

- `scripts/wp_publish.py` — publishes to WordPress via REST API with an
  idempotency key (dry-run by default).
- `scripts/meta_publish.py` — publishes to Meta via Graph API with an
  idempotency key (dry-run by default).
- `scripts/reconcile.py` — reconciles WP vs Meta state when the result is
  unknown; emits a delta report.
