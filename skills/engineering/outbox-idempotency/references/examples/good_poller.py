# Good poller: ORDER BY created_at, FOR UPDATE SKIP LOCKED, UPDATE sent_at, no DELETE.
def poll():
    rows = db.execute(
        "SELECT * FROM outbox "
        "WHERE sent_at IS NULL AND attempts < 5 "
        "ORDER BY created_at "
        "FOR UPDATE SKIP LOCKED LIMIT 50"
    ).fetchall()
    for row in rows:
        publish(row.payload)
        db.execute(
            "UPDATE outbox SET sent_at = now() WHERE id = ?", row.id
        )
        if row.attempts >= 5:
            db.execute(
                "INSERT INTO poison_outbox (id, idempotency_key, payload) "
                "VALUES (?, ?, ?) ON CONFLICT DO NOTHING", row.id, row.key, row.payload
            )
