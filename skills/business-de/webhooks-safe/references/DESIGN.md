# DESIGN: webhooks-safe

## Trigger description (SKILL.md description draft, <=1024 chars)
"Ingest inbound webhooks safely for Ottili flows: verify signatures, dedupe, preserve order, respect replay windows and route failures to a dead-letter queue, all without SSRF on delivery. Use when an agent must receive, verify or process a webhook payload; when a webhook arrives out of order or twice; or when a webhook handler fails. Not for outbound retry engineering (that lives in the engineering playbooks)."

## Procedure outline
1. **Verify the signature** — recompute the HMAC over the raw body with the provider's secret; reject if it does not match. Never trust headers alone.
2. **Dedupe** — every webhook carries an event id; store the id with a TTL; on a duplicate id, ack and skip. Never process twice.
3. **Preserve order** — within a single delivery stream, process events in arrival order; if an event is out of sequence, hold it until the missing event arrives or the replay window expires.
4. **Respect replay windows** — if a provider guarantees delivery within N minutes, hold unprocessed events for that window before declaring them lost.
5. **Dead-letter** — on persistent failure, move the event to a dead-letter queue with the raw payload and the failure reason; never silently drop.
6. **SSRF-safe delivery** — if the skill ever needs to deliver, validate the target URL against an allow-list of Ottili endpoints; never deliver to arbitrary hosts.
7. **Log** — record every verify/dedupe/delivery decision with the event id.

## Scripts planned
- `scripts/verify.py` — verifies a webhook signature against the raw body.
- `scripts/dedupe.py` — checks and records an event id with a TTL.
- `scripts/deadletter.py` — moves a failed event to the dead-letter queue.

## Five eval prompts
1. "A webhook arrives with a bad signature. What do we do?" -> must reject, log and not process.
2. "The same event id arrives twice. What do we do?" -> must ack and skip the second, never process twice.
3. "Events arrive out of order. What do we do?" -> must hold the out-of-sequence event until the missing one arrives or the replay window expires.
4. "Our webhook handler keeps failing. What do we do?" -> must move the event to the dead-letter queue with the raw payload and reason.
5. "We need to deliver a webhook to a URL. Which URLs are allowed?" -> must name the allow-list rule and reject arbitrary hosts (SSRF-safe).

## What this skill does better than generic agents
- Encodes signature verification over the raw body, not just header checking.
- Treats dedupe, order and replay windows as explicit steps with a TTL, which generic agents skip.
- Adds the SSRF-safe delivery allow-list, which is missing from most webhook skills.
