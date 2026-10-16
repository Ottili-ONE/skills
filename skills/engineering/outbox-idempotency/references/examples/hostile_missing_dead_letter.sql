-- HOSTILE: complete envelope but the state never reaches dead_letter, so a poison row
-- blocks the queue forever. The poison threshold is unreachable by construction.
CREATE TABLE IF NOT EXISTS audit_outbox (
    company_id   TEXT NOT NULL,
    outbox_id    TEXT NOT NULL,
    audit_id     TEXT NOT NULL,
    enqueued_at  TEXT NOT NULL,
    record       TEXT NOT NULL,
    delivered_at TEXT,
    receipt_hash TEXT,
    PRIMARY KEY (company_id, outbox_id)
);
INSERT INTO audit_outbox (company_id, outbox_id, audit_id, enqueued_at, record)
VALUES ('co_1', 'ob_1', 'audit_1', now(),
        '{"schema_version":"ottili.outbox-record/v1","outbox_id":"ob_1","company_id":"co_1",'
        '"event_id":"evt_1","event_type":"order.created","partition_key":"co_1",'
        '"state":"pending","attempts":0,"created_at":"2026-10-16T00:00:00.000Z",'
        '"dispatched_at":null,"payload_digest":"sha256:abc","last_error_code":null,'
        '"available_at":"2026-10-16T00:00:00.000Z","dispatch_lease_expires_at":null,'
        '"dispatch_fence":null}');
