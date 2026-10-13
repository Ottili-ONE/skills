# Bad poller: ORDER BY on the primary key, not created_at. Outbox order is publish
# order, which is created_at order; ordering by id delivers rows in insertion order
# and can re-order events for ordering-dependent consumers.
def poll():
    rows = db.execute(
        "SELECT * FROM outbox WHERE sent_at IS NULL "
        "ORDER BY id FOR UPDATE SKIP LOCKED LIMIT 50"
    ).fetchall()
    for row in rows:
        publish(row.payload)
        db.execute("UPDATE outbox SET sent_at = now() WHERE id = ?", row.id)
