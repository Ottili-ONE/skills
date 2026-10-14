# EVALS — outbox-idempotency
Retrieval date: 2026-10-13. Verified versions: PostgreSQL 15+ (18 confirmed);
Kafka 3.7; RFC 9110 §9.2.2. Sources: references/SOURCES.md.

Each prompt lists expected behaviour, failure signs, and the exact command that proves it.

## E1 — idempotency key generated before commit
**Prompt**: "Generate the idempotency key inside the poller, after the business row exists."
**Expected**: rejected — the key must be generated **before** the business transaction
commits, so a retry can never double-publish.
**Failure sign**: agent puts key generation in the poller.
**Worked example good**: `BEGIN; INSERT business; idempotency_key = gen_random_uuid();
INSERT outbox (...); COMMIT;`
**Worked example bad**: poller does `SELECT ... FOR UPDATE` then generates the key.

## E2 — poller ordering
**Prompt**: "My poller does `SELECT id, payload FROM outbox WHERE sent_at IS NULL
LIMIT 50 FOR UPDATE SKIP LOCKED`."
**Expected**: flagged — missing `ORDER BY created_at`. Delivery order is then undefined
and ordering-dependent consumers break.
**Failure sign**: agent says the LIMIT makes it deterministic.
**Exact command to verify**: grep the poller source for `ORDER BY created_at`; absent = drift.

## E3 — poison handling
**Prompt**: "After 5 failed attempts, my poller deletes the row."
**Expected**: rejected — move it to `poison_outbox` with the error snapshot. Deleting a
poison row is a lost event with no audit trail.
**Failure sign**: agent says "we do not need dead letters".
**Worked example good**: `INSERT INTO poison_outbox SELECT * FROM outbox WHERE
attempts >= 5; DELETE FROM outbox WHERE attempts >= 5;` — no, DELETE is still wrong;
the row must be **moved**, not deleted.

## E4 — replay preserves the key
**Prompt**: "I fixed the root cause. How do I replay the poison rows?"
**Expected**: `SELECT id, idempotency_key, payload FROM poison_outbox ORDER BY
created_at;` re-publish, keeping the original `idempotency_key` so the consumer's dedup
still works.
**Failure sign**: agent generates new keys on replay, causing double-delivery.
**Worked example good**: replayed row carries the same `idempotency_key` it had when first
published.

## E5 — one-transaction write
**Prompt**: "My service does `INSERT INTO business` in one transaction and
`INSERT INTO outbox` in a second, later transaction."
**Expected**: rejected — a connection drop between the two commits loses the event
forever. Both inserts must be in ONE transaction.
**Failure sign**: agent says "we have retries, so it is fine".
**Worked example good**: `BEGIN; INSERT business; INSERT outbox; COMMIT;`
**Worked example bad**: two separate commits with no shared transaction.

## E6 — duplicate publish on crash
**Prompt**: "My poller publishes then crashes before `UPDATE sent_at = now()`."
**Expected**: the row is re-picked on restart and re-published — which is why the
`idempotency_key` exists. The consumer must dedupe; the publisher must not silently
skip the re-publish.
**Failure sign**: agent marks the row sent anyway, losing the event.

## Verification checklist
- [ ] Outbox table has UNIQUE `idempotency_key`
- [ ] Business write + outbox INSERT are in ONE transaction
- [ ] Poller uses `ORDER BY created_at` + `FOR UPDATE SKIP LOCKED`
- [ ] Poison threshold moves rows after `max_attempts` (never deletes)
- [ ] Replay preserves the original `idempotency_key`
- [ ] Leak test harness runs green against Docker Postgres
- [ ] No DELETE on `poison_outbox` rows

## Near-miss prompts (act before the incident)
- **N1 — "We have retries, so the outbox doesn't need a UNIQUE constraint."** Answer: no. Retries are the reason the constraint exists; without it a crash mid-publish duplicates the event.
- **N2 — "The business write and the outbox INSERT are in separate transactions, that's fine."** Answer: no. Two transactions can never be atomic; use one transaction or lose the event on crash.
- **N3 — "Just DELETE the poison row after max_attempts."** Answer: no. Move it to `poison_outbox` and keep it for audit; deletion hides the failure.
- **N4 — "The poller doesn't need `FOR UPDATE SKIP LOCKED` if there is only one."** Answer: no. A second poller is always added later; the ordering and locking are part of the contract.
- **N5 — "Replay can reuse the old idempotency key."** Answer: no. Replay preserves the original key so the consumer dedupes correctly; a new key would double-deliver.
