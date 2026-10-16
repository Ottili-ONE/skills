-- HOSTILE: audit_outbox shape on paper but company_id is missing from the envelope and
-- the PRIMARY KEY is not tenant-scoped. Idempotency would then be global, so a retry
-- in company B could re-deliver company A's event.
CREATE TABLE IF NOT EXISTS audit_outbox (
    outbox_id    TEXT NOT NULL,
    audit_id     TEXT NOT NULL,
    enqueued_at  TEXT NOT NULL,
    record       TEXT NOT NULL,
    delivered_at TEXT,
    receipt_hash TEXT,
    PRIMARY KEY (outbox_id)
);
INSERT INTO audit_outbox (company_id, outbox_id, audit_id, enqueued_at, record)
VALUES (NULL, 'ob_1', 'audit_1', now(),
        '{"schema_version":"ottili.outbox-record/v1","outbox_id":"ob_1",'
        '"event_id":"evt_1","event_type":"order.created","partition_key":"co_1",'
        '"state":"pending","attempts":0,"created_at":"2026-10-16T00:00:00.000Z",'
        '"dispatched_at":null,"payload_digest":"sha256:abc","last_error_code":null,'
        '"available_at":"2026-10-16T00:00:00.000Z","dispatch_lease_expires_at":null,'
        '"dispatch_fence":null}');
