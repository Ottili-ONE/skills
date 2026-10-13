-- Bad: poison rows are deleted instead of moved.
CREATE TABLE IF NOT EXISTS outbox (
    id              bigint      PRIMARY KEY,
    idempotency_key text        NOT NULL UNIQUE,
    payload         jsonb       NOT NULL,
    attempts        int         NOT NULL DEFAULT 0,
    sent_at         timestamptz,
    created_at      timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS poison_outbox (
    id              bigint      PRIMARY KEY,
    idempotency_key text        NOT NULL
);
DELETE FROM poison_outbox WHERE id = 1;
