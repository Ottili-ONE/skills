# Bad poller: no max_attempts / attempts >= N threshold; poison never triggers.
def poll():
    rows = db.execute(
        "SELECT * FROM outbox WHERE sent_at IS NULL "
        "ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 50"
    ).fetchall()
    for row in rows:
        publish(row.payload)
        db.execute("UPDATE outbox SET sent_at = now() WHERE id = ?", row.id)
