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
COMMIT;
