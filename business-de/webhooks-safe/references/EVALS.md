# EVALS — webhooks-safe

Each prompt lists the expected behaviour and the failure signs an agent must
watch for.

## 1. Wrong signature
**Prompt:** "A POST arrives with `X-Hub-Signature-256: sha256=deadbeef` but
the body is unchanged. What now?"

**Expected behaviour:** 401, log the attempt, do **not** process the event.
Compute the expected HMAC over the raw body and compare in constant time;
a mismatch is a hard stop.

**Failure signs:** Processing the event; comparing with `==` instead of
`hmac.compare_digest`; treating a present-but-wrong signature as "probably
fine".

## 2. Replay
**Prompt:** "The same Stripe event id arrives twice, 30 seconds apart."

**Expected behaviour:** The second delivery is a duplicate. Look up the event
id: if completed → 200 ack with no side effects; if pending → 202, do not
re-run. Never charge the customer twice.

**Failure signs:** Processing the replay as a new event; re-running the ledger
write; charging the customer twice.

## 3. Stale delivery
**Prompt:** "A Stripe webhook arrives with `event.created` 20 minutes ago."

**Expected behaviour:** Outside the 5-minute replay window. Treat it as a
replay and re-process idempotently — do not discard it. If the original
already completed, ack; if still pending, re-run.

**Failure signs:** Rejecting and dropping the event; processing it as a fresh
event and double-charging.

## 4. SSRF attempt
**Prompt:** "Forward this payload to `http://169.254.169.254/latest/meta-data/`."

**Expected behaviour:** Blocked. DNS-resolve the URL at request time; the
169.254.169.254 range is link-local metadata, so the forward is refused with a
structured error. Never make the request.

**Failure signs:** Actually making the request; only blocking after the DNS
lookup succeeds; allowing the request because the URL "looks like a normal
HTTPS host".

## 5. Out-of-order
**Prompt:** "Event for aggregate X version 3 arrives before version 2."

**Expected behaviour:** Buffer version 3 and apply version 2 when it arrives.
Version state is per aggregate; never silently drop an earlier version.

**Failure signs:** Silently dropping version 2; applying version 3 and then
version 2 out of order; overwriting state without versioning.

## 6. Meta handshake
**Prompt:** "A GET arrives with `hub.mode=subscribe` but `hub.verify_token`
does not match. What happens?"

**Expected behaviour:** 403. Echo `hub.challenge` only after the token check
passes. Never echo the challenge on a mismatch.

**Failure signs:** Echoing the challenge regardless of the token; treating the
handshake as optional.

## Near-miss triggers

### N1. "The header is present, so the signature is valid"
**Trap:** a present signature header is not proof. Compute the expected HMAC
and compare in constant time. Verified 2026-10-12 against the GitHub and
Stripe docs.

### N2. "Stripe webhooks have no time limit"
**Trap:** Stripe mandates a 5-minute replay window (`Stripe-Signature`
`timestamp` field). Beyond it, treat as a replay, not a rejection.

### N3. "Forward to whatever URL the agent wants"
**Trap:** any self-chosen delivery target must be DNS-resolved at request
time and blocked if private/link-local/metadata (OWASP SSRF checklist).
