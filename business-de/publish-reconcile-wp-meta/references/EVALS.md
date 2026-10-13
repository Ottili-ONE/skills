# EVALS — publish-reconcile-wp-meta

Each prompt lists the expected behaviour and the failure signs an agent must
watch for.

## 1. Retry without idempotency key
**Prompt:** "Publish the same post twice with a network blip in between."

**Expected behaviour:** The second call returns the **existing** post because
`client_reference` is reused. Never create a duplicate.

**Failure signs:** Two live posts for one order; a new `client_reference` on
retry.

## 2. Unknown result
**Prompt:** "Meta returned `id: 123_456` and HTTP 200, but the GET on
`123_456` returns an error."

**Expected behaviour:** Status is `unknown`, not `published`; retry with
backoff. A 2xx with an id is not proof.

**Failure signs:** Marking it published; stopping retries after the first
publish 2xx.

## 3. WP auth failure
**Prompt:** "The Application Password was rotated."

**Expected behaviour:** The publish fails with a structured auth error; the row
stays `unknown` and is escalated, not silently retried forever.

**Failure signs:** Retrying the same request indefinitely; treating a 401 as a
transient network error.

## 4. Dual-platform mismatch
**Prompt:** "The post is live on WP but Meta returned an error."

**Expected behaviour:** The reconciliation row shows per-provider status; the
overall record is `partial`. Escalate the Meta side.

**Failure signs:** Reporting the whole publish as succeeded; marking both as
published because one worked.

## 5. Re-read by id
**Prompt:** "A post was published an hour ago. How do you know it is still
live?"

**Expected behaviour:** Re-read by id on demand; only a successful read with
the expected content counts as `published`. Never trust the original 2xx.

**Failure signs:** Trusting the original 2xx forever; not re-reading on
demand; recording `published` without a read.

## Near-miss triggers

### N1. "Meta returned an id, so it is published"
**Trap:** Meta can return 2xx and later reject the post (moderation). Always
re-read by id and record `unknown` until observable. Verified 2026-10-12
against the Meta Page Feed docs.

### N2. "Both providers succeeded, so the publish is done"
**Trap:** one provider may fail silently. The overall record is `partial`
unless both reads return the expected content.

### N3. "WordPress webhooks will tell us when the post is live"
**Trap:** WP has no native inbound webhook (developer.wordpress.org/rest-api/,
verified 2026-10-12). Reconcile by polling the REST API or a plugin webhook.
