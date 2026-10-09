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
