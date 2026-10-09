# EVALS — publish-reconcile-wp-meta

Each prompt lists the expected behaviour and the failure signs an agent must
watch for. The offline scripts (`scripts/wp_publish.py`, `scripts/meta_publish.py`,
`scripts/reconcile.py`) are run in dry-run mode and their output compared to
the expected behaviour. Tests live in `tests/test_publish.py`.

## 1. Publish this post to WordPress twice with the same idempotency key.

**Prompt:** "Publish this post to WordPress twice with the same idempotency key."

**Expected behaviour:** Both calls carry the same client-generated idempotency
key. The skill stores the key -> post id mapping; the second call returns the
stored post id and never creates a second post. Detect: two distinct `id`
values for one key is a failure.

**Failure signs:** Two posts created; no idempotency key; key differs between calls.

## 2. Meta returns HTTP 409 on publish.

**Prompt:** "Meta returns HTTP 409 on publish."

**Expected behaviour:** Treat 409 as conflict/duplicate. Re-query by idempotency
key; never retry blindly and never re-create. Auth errors (401/403) are
re-issued, never retried with the same token.

**Failure signs:** Blind retry; re-creating on 409; retrying auth errors.

## 3. The publish call times out with no response.

**Prompt:** "The publish call times out with no response."

**Expected behaviour:** Treat as an unknown result. Re-query both WordPress and
Meta by the idempotency key, compare state, log the delta. Never assume the
first (missing) response is authoritative.

**Failure signs:** Assuming success; assuming failure; not re-querying both platforms.

## 4. Reconcile this post between WordPress and Meta.

**Prompt:** "Reconcile this post between WordPress and Meta."

**Expected behaviour:** Compare state on both platforms and report match/mismatch
with the delta. Exit 0 on match, exit 1 on mismatch. A persistent mismatch is
flagged for human review and never silently overwritten.

**Failure signs:** Comparing only one platform; returning ok on a mismatch;
silent overwrite.

## 5. Can we publish to any URL?

**Prompt:** "Can we publish to any URL?"

**Expected behaviour:** No. Publish only to the configured WordPress and Meta
endpoints. An attacker-controlled content field that triggers a publish to an
arbitrary host is an SSRF — validate the target against the allow-list, never
publish to arbitrary hosts.

**Failure signs:** Publishing to an arbitrary host; omitting the allow-list check;
treating content fields as trusted.

## 6. The idempotency store already has our key. What do we do?

**Prompt:** "The idempotency store already has our key for WordPress. What do we do?"

**Expected behaviour:** Look up the key before publishing. If it exists, return the stored post id and never create a second post. The `idempotency_store.py --lookup` helper exits 0 with `found: true` and the stored `post_id`. The store is append-only JSONL — never mutate an entry in place.

**Failure signs:** Publishing again despite a stored mapping; mutating the store entry; treating a lookup miss as a reason to publish.

## 7. WP Basic Auth is deprecated. What do we use?

**Prompt:** "WP Basic Auth is deprecated. What do we use?"

**Expected behaviour:** Use Application Passwords or OAuth2. Basic Auth is deprecated in WP 6.7+ (core); the plugin ships separately and is unmaintained. The `wp_publish.py` helper documents this and the config pins the WP version.

**Failure signs:** Recommending the Basic Auth plugin as the production path; hardcoding the WP version instead of reading it from config.
