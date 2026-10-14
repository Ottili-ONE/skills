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

## 8. Meta's API version is pinned at v19.0. Is that the newest?

**Prompt:** "Meta's API version is pinned at v19.0. Is that the newest?"

**Expected behaviour:** No. The Graph API changelog already lists v20.0 and
v21.0 alongside the pinned v19.0 (re-verified 2026-10-09). The pin stays at
v19.0 until the Ottili integration is explicitly bumped — never assume the
pinned version is current. Meta sunsets versions without notice, so re-verify
the changelog quarterly.

**Failure signs:** Bumping to v21.0 without a migration review; assuming
v19.0 is the newest; hardcoding the version instead of reading it from
config.

## 9. Reconcile with `--strict`. What changes?

**Prompt:** "Reconcile with `--strict`. What changes?"

**Expected behaviour:** Strict mode fails on *missing* fields, not just
mismatches. If either platform lacks `id`, `status` or the idempotency key,
the report is non-ok (exit 1). Without `--strict`, missing fields are
skipped. Use strict mode for audit-grade reconciliation.

**Failure signs:** Treating strict mode as a retry flag; returning ok when a
field is absent; omitting the `--strict` flag in an audit context.

## Near-miss triggers

Prompts that look fine at first glance but hide a trap. The agent must catch
the trap and still produce a passing artefact.

### N1. "Publish to WordPress, the URL is ours"
**Trap:** outbound publish is allow-listed. An arbitrary URL — even one that
belongs to Ottili — is rejected unless it is in the allow-list. The check is
on the target, not the content.

### N2. "The idempotency store is just a cache, delete the key on success"
**Trap:** the store is append-only and part of the audit trail. Deleting a
key hides the fact that the post was published twice. Keep every key for the
GoBD retention period.

### N3. "Meta returned 409, so retry with a new key"
**Trap:** 409 on Meta is the idempotency conflict — the post exists. A new
key makes it a *new* post and duplicates content. Reconcile by reference
first; only a genuinely new reference may be retried.

### N4. "Reconcile WP and Meta, they should match"
**Trap:** the two platforms have different field sets (WP has `slug`,
Meta has `id`/`link`). Compare only the shared fields
(`id`, `status`, idempotency key); report platform-specific fields as
informational, not as deltas.

### N5. "WP Basic Auth still works, use it"
**Trap:** Basic Auth is deprecated in WP 6.7+ core and the replacement plugin
is unmaintained. The config pins the WP version; the helper must read it and
warn. A green run that uses Basic Auth on WP 6.7+ is a failure sign.


---

## Run these checks

Every prompt above names a script and an expected exit code. This section
gives the exact, copy-paste-safe commands and the output an agent must see.
All commands are run from the skill directory
(`cd skills/business-de/publish-reconcile-wp-meta`). The idempotency store is
append-only JSONL — never delete a key on success, it is part of the audit
trail (see `gobd-archive`).

```bash
# 8. publish to Meta, idempotent -> exit 0
python3 scripts/meta_publish.py --key ORD-1 --page-id 123
# "idempotency_field": "idempotency_key", embedded in the POST body

# 8b. WP version pin -> exit 0
python3 scripts/wp_publish.py --key ORD-1 --dry-run
# reads the pinned WP version from config; warns on Basic Auth + WP 6.7+

# 9. reconcile matching platforms -> exit 0
python3 scripts/reconcile.py --key ORD-1 --wp evals_fixtures/wp_match.json --meta evals_fixtures/meta_match.json
# {"ok": true, "deltas": []}

# 9b. reconcile mismatch -> exit 1
python3 scripts/reconcile.py --key ORD-1 --wp evals_fixtures/wp_match.json --meta evals_fixtures/meta_draft.json
# {"ok": false, "deltas": [{"field": "status", "match": false}]}

# 9c. reconcile --strict on a missing idempotency key -> exit 1
python3 scripts/reconcile.py --key ORD-1 --wp evals_fixtures/wp_nokey.json --meta evals_fixtures/meta_match.json --strict
# {"ok": false, "strict": true, "deltas": [{"reason": "key mismatch"}]}
```

The two platforms have different field sets (WP has `slug`, Meta has
`id`/`link`); compare only the shared fields (`id`, `status`, idempotency
key) and report platform-specific fields as informational.
