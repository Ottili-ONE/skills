# Procedures — publish-reconcile-wp-meta

All endpoints, credential methods and versions are read from
`config/versions.json` (never hardcode). Re-verify each provider's API
contract before every build and record the retrieval date in
`references/SOURCES.md`.

## 1. Idempotent publish

Every publish call carries a client-generated idempotency key. The key is
your own content reference; it must be stable across retries. On a duplicate
key the platform returns the existing post id — never create a second.

**POST is not idempotent by HTTP semantics** (RFC 9110). Neither WP nor Meta
natively supports idempotency keys, so the skill implements idempotency in a
reconciliation layer: the `scripts/idempotency_store.py` helper stores the
key → post id mapping in an append-only JSONL file, and on a duplicate key
it returns the stored post id. Never mutate an entry in place.

**Check before you send:**
```bash
python3 idempotency_store.py --key ORD-1 --platform wordpress --lookup --store /tmp/ids.jsonl
```
If `found: true`, stop and return the stored `post_id`. If `found: false`,
publish, then record the mapping:
```bash
python3 idempotency_store.py --key ORD-1 --platform wordpress --post-id 42 --store /tmp/ids.jsonl
```

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
Detect it: two distinct `id` values for the same idempotency key. The
idempotency store should have recorded the first one.

## 3. Meta path

- Endpoint: `https://graph.facebook.com/v19.0/{page-id}/feed`
- Auth: page access token in the `access_token` query parameter or header.
- Create: `POST /{page-id}/feed` with `message`, `published`.
- Update: `POST /{post-id}` (same body).
- Meta sunsets API versions silently; the changelog already lists v20.0 and
  v21.0 alongside the pinned v19.0 (re-verified 2026-10-09). Pin the version
  in config and re-verify quarterly; do not assume v19.0 is the newest.

```bash
curl -s -X POST "https://graph.facebook.com/v19.0/123456789/feed" \
  -d "access_token=$PAGE_TOKEN" \
  -d "message=Hello"
```

## 4. Handling errors

The full error → fix mapping lives in the SKILL.md decision table. In
procedure form:

- **400** — validation error. Fix the named field in the request body; do
  not retry as-is.
- **401 / 403** — auth failure. Re-issue credentials; never retry with the
  same token.
- **409** — conflict / duplicate. Re-query by idempotency key; never
  re-create.
- **429** — rate limited. Exponential backoff, up to 3 attempts.
- **5xx** — platform outage. Backoff; mark the post unknown and reconcile
  later.

Retry budget: 3 attempts, base 500 ms, factor 2, cap 30 s. Auth errors are
never retried with the same token.

## 5. Reconciling unknown results

If the response is ambiguous (timeout, partial success), re-query both APIs
by idempotency key and log the delta between WP and Meta states. The full
outcome table lives in the SKILL.md decision table. In procedure form:

- Both platforms match → ok, log.
- One platform newer → re-query the older, log the delta.
- Unknown result (timeout) → re-query both by idempotency key, log the delta.
- Persistent mismatch → flag for human review; never silently overwrite.

## 6. SSRF-safe delivery

Publish only to the configured WP/Meta endpoints. Never publish to arbitrary
hosts — an attacker-controlled content field that triggers a publish to an
arbitrary host is an SSRF. Validate the target against the allow-list; reject
IP literals and `localhost` without resolving them.

## 7. Offline helper scripts

- `scripts/wp_publish.py` — publishes to WordPress via REST API with an
  idempotency key (dry-run by default).
- `scripts/meta_publish.py` — publishes to Meta via Graph API with an
  idempotency key (dry-run by default).
- `scripts/idempotency_store.py` — append-only key → post id store; lookup
  before every publish.
- `scripts/reconcile.py` — reconciles WP vs Meta state when the result is
  unknown; emits a delta report; `--strict` fails on missing fields.
