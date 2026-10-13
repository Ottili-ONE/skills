# Procedures — publish-reconcile-wp-meta

Versions are pinned in `config/versions.json`; never hardcode a version.

## 1. Normalize

```json
{"client_reference": "ord-2026-0001", "title": "...", "body": "...",
 "status": "publish", "media": [{"type":"image","url":"..."}]}
```

## 2. Publish to WordPress

```bash
curl -s -X POST "https://wp.example.com/wp-json/wp/v2/posts" \
  -u "username:Application Password" \
  -H "Content-Type: application/json" \
  -d @canonical.json
```

Capture `id` and `link`. Auth is Basic (Application Password) or OAuth 2
(developer.wordpress.org/rest-api/authentication/, verified 2026-10-12).

## 3. Publish to Meta

```bash
curl -s -X POST "https://graph.facebook.com/v26.0/{page-id}/feed" \
  -d "message=..." -d "access_token=PAGE_TOKEN"
```

Response shape: `data[].id` = `{page-id}_{post-id}`. Requires
`pages_manage_posts` + `pages_read_engagement` (developers.facebook.com,
verified 2026-10-12).

## 4. Reconcile

Re-read each post by id **before** recording success:

| Read result | Status |
|---|---|
| expected content | `published` |
| draft / error response | `unknown`, retry with backoff |
| 404 | `unknown`, escalate |

A 2xx at publish time is never proof. Record the reconciliation row:

```json
{"provider": "meta", "client_reference": "ord-2026-0001",
 "remote_id": "123_456", "status": "unknown", "attempts": 1,
 "last_checked_at": "2026-10-13T00:00:00Z"}
```

## 5. Dual-platform consistency

If WP is `published` and Meta is `unknown`, the overall record is `partial`,
not `published`. Never report the whole publish as succeeded.

## Worked examples

### Good — both platforms observable

```
WP:  GET /wp-json/wp/v2/posts/42  -> 200, status "publish", link matches
Meta: GET /v26.0/123_456         -> 200, message matches
=> published
```

### Bad — trusting the publish 2xx

```
Meta POST -> 200 {data:{id:"123_456"}}
Agent marks published without re-reading.
Later: GET /v26.0/123_456 -> error (moderation).
=> the publish was never observable; status should have been unknown.
```
