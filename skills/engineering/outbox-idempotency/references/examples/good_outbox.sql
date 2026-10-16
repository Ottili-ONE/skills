-- Good outbox: UNIQUE idempotency_key, attempts, sent_at, poison_outbox, same-transaction writes.
CREATE TABLE IF NOT EXISTS outbox (
    id              bigint      PRIMARY KEY DEFAULT nextval('outbox_id_seq'),
    idempotency_key text        NOT NULL UNIQUE,
    payload         jsonb       NOT NULL,
    attempts        int         NOT NULL DEFAULT 0,
    sent_at         timestamptz,
    created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS poison_outbox (
    id              bigint      PRIMARY KEY,
    idempotency_key text        NOT NULL,
    payload         jsonb       NOT NULL,
    moved_at        timestamptz NOT NULL DEFAULT now()
);

BEGIN;
INSERT INTO orders (id, total) VALUES (1, 99);
INSERT INTO outbox (idempotency_key, payload)
VALUES ('order-1', '{"event":"order.created"}');
INSERT INTO audit_outbox (company_id, outbox_id, audit_id, enqueued_at, record)
VALUES ('co_1', 'ob_2', 'audit_2', now(),
        '{"schema_version":"ottili.outbox-record/v1","outbox_id":"ob_2","company_id":"co_1",'
        '"event_id":"evt_2","event_type":"order.created","partition_key":"co_1",'
        '"state":"dead_letter","attempts":5,"created_at":"2026-10-16T00:00:01.000Z",'
        '"dispatched_at":null,"last_error_code":"consumer_dead",'
        '"payload_digest":"sha256:def","available_at":null,'
        '"dispatch_lease_expires_at":null,"dispatch_fence":null}');
COMMIT;
