-- Bad: idempotency_key is not unique -> duplicate publishes under retry.
CREATE TABLE IF NOT EXISTS outbox (
    id              bigint      PRIMARY KEY,
    idempotency_key text        NOT NULL,
    payload         jsonb       NOT NULL,
    attempts        int         NOT NULL DEFAULT 0,
    sent_at         timestamptz,
    created_at      timestamptz NOT NULL DEFAULT now()
);
