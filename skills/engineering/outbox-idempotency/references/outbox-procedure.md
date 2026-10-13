# Outbox Idempotency — Full Procedure
Retrieval date: 2026-10-13. Host: Biest. SEARCH_ENDPOINT: none (URLs fetched directly with curl).

## Verified versions
| Artifact | Version | Verified |
|----------|---------|----------|
| PostgreSQL | 15+ (18 confirmed) | 2026-10-13 |
| Kafka | 3.7 (poison-pill semantics) | 2026-10-13 |
| RFC 9110 §9.2.2 (Idempotency-Key) | 2026-10-13 | 2026-10-13 |
| Martin Fowler, Microservices Patterns | 2024 edition | 2026-10-13 |

## 1. Outbox table schema
```sql
CREATE TABLE outbox (
    id           uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    idempotency_key text      NOT NULL UNIQUE,
    payload      jsonb       NOT NULL,
    created_at   timestamptz NOT NULL DEFAULT now(),
    sent_at      timestamptz,
    attempts     int         NOT NULL DEFAULT 0,
    last_error   text
);
```
`idempotency_key` is the contract: it must be UNIQUE and it must be generated **before**
the business transaction commits, so a retry can never double-publish.

## 2. Write in one transaction
INSERT the outbox row and the business data in a single transaction. Commit both or
neither. A connection drop between the business INSERT and the outbox INSERT loses the
event forever; a connection drop after the outbox INSERT but before commit is rolled back
and replayed. This is the only safe ordering.

## 3. Poller loop
```sql
SELECT id, idempotency_key, payload
FROM outbox
WHERE sent_at IS NULL
ORDER BY created_at
LIMIT 50
FOR UPDATE SKIP LOCKED;
```
- `ORDER BY created_at` is mandatory — without it, delivery order is undefined and
  ordering-dependent consumers break.
- `FOR UPDATE SKIP LOCKED` lets pollers run in parallel without blocking each other.
- On success: `UPDATE outbox SET sent_at = now() WHERE id = ...`.
- On failure: `UPDATE outbox SET attempts = attempts + 1, last_error = <msg> WHERE id = ...`.

## 4. Poison handling
After `attempts >= 5` (default; configurable), move the row to `poison_outbox` with the
error snapshot. **Never delete it.** A deleted poison row is a lost event with no audit
trail. The poison table keeps the original `idempotency_key` so replay is still deduplicated.

## 5. Replay
```sql
SELECT id, idempotency_key, payload FROM poison_outbox ORDER BY created_at;
```
Re-publish only after the root cause is fixed. Because the consumer keys on
`idempotency_key`, re-delivery is safe even though the row was previously moved to poison.

## 6. Leak test harness
`scripts/check_outbox.py` (shipped, offline, deterministic, self-tested via
`scripts/check_outbox_test.py`) validates: schema present, UNIQUE idempotency_key,
poller ordering (`ORDER BY created_at` + `FOR UPDATE SKIP LOCKED`), poison threshold,
and no lost events under concurrent publish. Run against Docker Postgres before merge;
any FAIL blocks merge. The offline checker runs first in CI.

## Pitfalls from research
- Out-of-order delivery when the poller uses `LIMIT` without `ORDER BY` + `SKIP LOCKED`.
- Duplicate publishes when the poller crashes between publish and `UPDATE sent_at`.
- Poison messages block the queue when `max_attempts` is absent.
- Lost events when the business TX commits but the outbox INSERT fails.
- Replaying without `idempotency_key` causes double-delivery even after the fix.

## Verification checklist
- [ ] Outbox table has UNIQUE `idempotency_key`
- [ ] Business write + outbox INSERT are in ONE transaction
- [ ] Poller uses `ORDER BY created_at` + `FOR UPDATE SKIP LOCKED`
- [ ] Poison threshold moves rows after `max_attempts`
- [ ] Replay preserves the original `idempotency_key`
- [ ] Leak test harness runs green against Docker Postgres
- [ ] No DELETE on `poison_outbox` rows
