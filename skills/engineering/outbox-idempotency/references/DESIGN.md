# DESIGN — outbox-idempotency

## Trigger description (draft)
Fires when: an agent designs or reviews a transactional outbox (write + event in one DB
transaction); when choosing an idempotency-key strategy; when a consumer retries a message and
must decide whether the side effect already happened; when diagnosing duplicate billing,
double emails, or reordered events; or when handling a poison message. Does NOT fire for:
fire-and-forget logging, or single-shot commands with no retry.

## What it does better than existing public skills
Existing outbox posts describe the pattern; none give the Ottili-specific decision procedure:
the key must be derived from the *business* identity (e.g. `invoice:<id>:<event>`), never a UUID
generated per attempt, because a UUID makes every retry look unique and defeats dedup. This
skill pins the ordering rule (per-aggregate stream, sequence via `INSERT ... ON CONFLICT`),
the poison-letter move to a `dead` table with `retry_count` and `last_error`, the replay
contract (replay is idempotent by construction), and the verification that a duplicate
publish does not produce a duplicate side effect. It also records the real incident: a
UUID-keyed outbox double-charged a customer when the publisher retried after a timeout.

## Procedure outline
1. Write the outbox row and the business change in ONE transaction (`BEGIN; UPDATE/INSERT;
   INSERT INTO outbox; COMMIT`). No outbox row without its business change, ever.
2. Derive the idempotency key from the business identity; never a per-attempt UUID.
3. Publish exactly once per outbox row: mark the row `published` only after the broker
   acknowledges; on failure, the row stays pending and the publisher retries.
4. Consumer: `BEGIN; SELECT ... FOR UPDATE WHERE key=?; IF already processed RETURN; do work;
   INSERT processed(key); COMMIT`. The dedup table is the source of truth.
5. Ordering: one stream per aggregate; sequence numbers from the outbox row id; consumers
   reorder by sequence and gap-detect.
6. Poison: after N retries, move to `dead` with the error; alert; never drop silently.

## Scripts planned
- `scripts/check_outbox.py` — scans migration/DML for outbox patterns: transaction wrapping,
   key derivation, published-flag, dead-letter table.

## Five eval prompts
1. "Generate a fresh UUID as the idempotency key for each publish attempt." → agent must reject;
   the key must come from business identity so retries dedupe.
2. "The consumer processed the message but the ack was lost." → the dedup table must already
   contain the key, so re-delivery is a no-op; agent must verify the `FOR UPDATE` guard.
3. "Events arrive out of order: invoice.paid before invoice.created." → agent must point to the
   per-aggregate sequence and the gap-detect rule, not assume ordering.
4. "A message keeps failing; how many retries before we give up?" → agent states N (default 5),
   then moves it to `dead` with `retry_count` and `last_error`, and alerts.
5. "Replay the outbox for tenant Acme after a fix." → agent replays by re-publishing pending
   rows; side effects must be idempotent by the dedup table, so no double charge.
