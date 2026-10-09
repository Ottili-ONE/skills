# EVALS — webhooks-safe

Each prompt lists the expected behaviour and the failure signs an agent must
watch for. The offline scripts (`scripts/verify.py`, `scripts/dedupe.py`,
`scripts/deadletter.py`) are run in dry-run mode and their output compared to
the expected behaviour. Tests live in `tests/test_webhooks.py`.

## 1. A webhook arrives with a bad signature. What do we do?

**Prompt:** "A webhook arrives with a bad signature. What do we do?"

**Expected behaviour:** Reject it immediately, log the decision with the event
id, and do not process it. Never dead-letter a bad signature — it is not our
event. Always verify over the raw body using `hmac.compare_digest`.

**Failure signs:** Processing the payload after a bad signature; dead-lettering
a bad signature; comparing with `==` instead of `hmac.compare_digest`;
verifying over the parsed body.

## 2. The same event id arrives twice. What do we do?

**Prompt:** "The same event id arrives twice. What do we do?"

**Expected behaviour:** Ack and skip the second delivery — never process it
twice. The dedupe store must be atomic (check-and-set in one operation) so a
race cannot process the event twice. The script output shows
`duplicate: true, action: ack_and_skip`.

**Failure signs:** Processing the event twice; a non-atomic check-then-set;
ignoring the TTL.

## 3. Events arrive out of order. What do we do?

**Prompt:** "Events arrive out of order. What do we do?"

**Expected behaviour:** Hold the out-of-sequence event until the missing one
arrives or the replay window expires. Ordering is enforced per delivery
stream, not globally — two independent providers can interleave.

**Failure signs:** Enforcing global ordering; dropping the out-of-sequence
event; processing it immediately.

## 4. Our webhook handler keeps failing. What do we do?

**Prompt:** "Our webhook handler keeps failing. What do we do?"

**Expected behaviour:** After 3 failures, move the event to the dead-letter
queue with the raw payload, the event id, the failure reason and the
timestamp. Never silently drop a webhook. The script output shows the event
id and reason.

**Failure signs:** Silently dropping the event; retrying forever; dead-lettering
without the raw payload.

## 5. We need to deliver a webhook to a URL. Which URLs are allowed?

**Prompt:** "We need to deliver a webhook to a URL. Which URLs are allowed?"

**Expected behaviour:** Only URLs on the allow-list of Ottili endpoints. An
attacker-controlled webhook payload that triggers an outbound call is an
SSRF — validate the target against the allow-list before delivering, never
deliver to arbitrary hosts.

**Failure signs:** Delivering to an arbitrary host; omitting the allow-list
check; treating the webhook payload's URL field as trusted.

## 6. Events arrive out of order. What do we do?

**Prompt:** "Events arrive out of order. What do we do?"

**Expected behaviour:** Hold the out-of-sequence event until the missing one
arrives or the replay window expires. Ordering is enforced per delivery
stream, not globally — two independent providers can interleave. The
`ordering.py` helper returns `action: hold` for a gap and `action: process`
when the sequence is in order. Old/duplicate sequences (`seq <= last_seq`)
return `duplicate_or_old` and exit 0.

**Failure signs:** Enforcing global ordering; dropping the out-of-sequence
event; processing it immediately; returning a non-zero exit for a
duplicate_or_old event.

## 7. We need to deliver a webhook to a URL. Which URLs are allowed?

**Prompt:** "We need to deliver a webhook to a URL. Which URLs are allowed?"

**Expected behaviour:** Only URLs on the allow-list of Ottili endpoints. An
attacker-controlled webhook payload that triggers an outbound call is an
SSRF — validate the target against the allow-list before delivering, never
deliver to arbitrary hosts. IP literals and `localhost` are rejected without
resolution. The `ssrf_check.py` helper exits 0 for allow-listed hosts and 1
otherwise.

**Failure signs:** Delivering to an arbitrary host; omitting the allow-list
check; treating the webhook payload's URL field as trusted; allowing a
loopback address.

## 8. PayPal's docs moved. What is verified?

**Prompt:** "PayPal's docs moved. What is verified?"

**Expected behaviour:** The old `docs/checkout/webhooks` paths all 404; the
live entry point is `developer.paypal.com/docs/api/webhooks/v1`. The
`X-PayPal-Signature` header name and algorithm are **unverified** at this
retrieval — the skill falls back to plain HMAC-SHA256 and flags the result.
Never treat PayPal as verified until a business account confirms the scheme.

**Failure signs:** Citing a 404'd PayPal path as authoritative; assuming the
PayPal scheme matches GitHub; hardcoding the PayPal header name in logic.
