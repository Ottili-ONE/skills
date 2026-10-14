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

## 6. A Stripe signature is older than 5 minutes. What do we do?

**Prompt:** "A Stripe signature is older than 5 minutes. What do we do?"

**Expected behaviour:** Reject it as a replay attack *before* checking the
HMAC. Stripe bakes the timestamp into the signature (`t=<ts>,v1=<hex>`); the
replay window is 5 minutes (pinned in config). The `verify.py` helper exits
non-zero and reports `replay_attack`. Never process a stale signature just
because the HMAC happens to verify.

**Failure signs:** Checking the HMAC first and accepting a stale signature;
hardcoding the replay window instead of reading it from config; treating an
old signature as "probably fine".

## 7. GitHub sends `X-Hub-Signature` (SHA1) instead of `X-Hub-Signature-256`.

**Prompt:** "GitHub sends `X-Hub-Signature` (SHA1) instead of `X-Hub-Signature-256`. What do we do?"

**Expected behaviour:** Reject it. The SHA1 header is deprecated; the skill
only accepts `X-Hub-Signature-256` with `sha256=<hex>`. Never fall back to
SHA1 — a downgrade is a strong sign of tampering.

**Failure signs:** Falling back to the SHA1 header; accepting a signature
format that the skill does not recognise; treating a missing `-256` header as
a normal case.

## 8. PayPal's docs moved. What is verified?

**Prompt:** "PayPal's docs moved. What is verified?"

**Expected behaviour:** The old `docs/checkout/webhooks` paths all 404; the
live entry point is `developer.paypal.com/docs/api/webhooks/v1` and the
overview is at `developer.paypal.com/docs/api/webhooks/overview`. The
`X-PayPal-Signature` header name and algorithm are **unverified** at this
retrieval — the skill falls back to plain HMAC-SHA256 and flags the result.
Never treat PayPal as verified until a business account confirms the scheme.

**Failure signs:** Citing a 404'd PayPal path as authoritative; assuming the
PayPal scheme matches GitHub; hardcoding the PayPal header name in logic.

## Near-miss triggers

Prompts that look fine at first glance but hide a trap. The agent must catch
the trap and still produce a passing artefact.

### N1. "The signature is valid, accept it"
**Trap:** a valid HMAC only proves the body matches the secret. The
timestamp is checked *before* the HMAC (Stripe's replay window). A valid
signature on a 6-minute-old event is still rejected.

### N2. "The event id is new, process it"
**Trap:** dedupe is per-stream. The same event id from a *different* stream
is not a duplicate. Conflating streams silently double-processes.

### N3. "Out of order, just buffer everything"
**Trap:** buffering grows without bound and masks a dead provider. The
skill holds only within the replay window; older events go to the
dead-letter queue with the reason, they are not silently dropped.

### N4. "Deliver the webhook to our staging URL"
**Trap:** the allow-list is checked on the target host, not the environment.
A staging host that is not allow-listed is rejected even if it "belongs to
us". SSRF prevention does not know ownership.

### N5. "The handler failed once, retry immediately"
**Trap:** a single failure routes to the dead-letter queue after the retry
budget is exhausted, not on the first failure. Immediate retry without
backoff is a thundering-herd risk on a failing upstream.


---

## Run these checks

Every prompt above names a script and an expected exit code. This section
gives the exact, copy-paste-safe commands and the output an agent must see.
All commands are run from the skill directory
(`cd skills/business-de/webhooks-safe`). `--now <unix-ts>` is REQUIRED for
Stripe/PayPal/Twilio: the replay window is enforced, not optional. The
signatures below were computed live over the shipped fixtures
(`evals_fixtures/body.json`, `evals_fixtures/stripe_body.json`) with secret
`s3cr3t` at `--now 1700000000`.

```bash
# 6. valid GitHub signature -> exit 0
python3 scripts/verify.py --provider github --secret s3cr3t --body evals_fixtures/body.json --sig 'sha256=d9d2c8a9b4fb9837fd759b9dd5fb3971338eb4c84e72b918168bfe94f3fa3abd'
# {"provider": "github", "valid": true}

# 6b. stale Stripe signature (600s old) -> exit 1 (replay attack)
python3 scripts/verify.py --provider stripe --secret s3cr3t --body evals_fixtures/stripe_body.json --sig 't=1700000000,v1=6576536b65241478ebe9103c3b5457d5cedf34588f900aa406741b133cef43d7' --now 1700000600
# {"provider": "stripe", "valid": false}

# 6c. Stripe without --now -> exit 2 (replay window enforced)
python3 scripts/verify.py --provider stripe --secret s3cr3t --body evals_fixtures/stripe_body.json --sig 't=1700000000,v1=6576536b65241478ebe9103c3b5457d5cedf34588f900aa406741b133cef43d7'
# {"ok": false, "error": "--now is required for stripe: the replay window is enforced, not optional"}

# 2. first delivery -> exit 0, process
python3 scripts/dedupe.py --event-id evt-1 --ttl 86400 --store /tmp/events.jsonl
# {"event_id": "evt-1", "duplicate": false, "action": "process"}

# 2b. second delivery -> exit 0, ack_and_skip
python3 scripts/dedupe.py --event-id evt-1 --ttl 86400 --store /tmp/events.jsonl
# {"event_id": "evt-1", "duplicate": true, "action": "ack_and_skip"}

# 3. in-order -> exit 0
python3 scripts/ordering.py --stream github:ottili --seq 1 --payload evals_fixtures/body.json --store /tmp/order.jsonl --replay-seconds 86400
# {"action": "process", "seq": 1, "released": []}

# 3b. out-of-sequence -> exit 1, held
python3 scripts/ordering.py --stream github:ottili --seq 3 --payload evals_fixtures/body.json --store /tmp/order.jsonl --replay-seconds 86400
# {"action": "hold", "held_count": 1, "reason": "waiting for missing event or replay-window expiry"}

# 4. dead-letter a failed event -> exit 0
python3 scripts/deadletter.py --event-id evt-9 --reason 'timeout' --payload evals_fixtures/body.json --queue /tmp/dl.jsonl
# {"event_id": "evt-9", "queued": "/tmp/dl.jsonl", "reason": "timeout"}

# 5. allow-listed target -> exit 0
python3 scripts/ssrf_check.py --url https://ottili.example/webhooks/inbound --allow ottili.example
# {"ok": true, "host": "ottili.example", "allowed": "ottili.example"}

# 5b. non-allow-listed target -> exit 1 (SSRF)
python3 scripts/ssrf_check.py --url https://evil.example/x --allow ottili.example
# {"ok": false, "reason": "host not in allow-list", "host": "evil.example"}
```

Dedupe is atomic (check-and-set under an advisory lock) so a race cannot
process the event twice. Ordering is per-stream, never global — two
independent providers may interleave. Verified 2026-10-14 against
`developer.paypal.com/docs/api/webhooks/v1` (HTTP 200; the
`X-PayPal-Signature` header name and algorithm remain **unverified** — the
skill falls back to plain HMAC-SHA256 and flags the result).
