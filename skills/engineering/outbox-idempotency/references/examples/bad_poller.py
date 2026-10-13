# Bad poller: no SKIP LOCKED, no ORDER BY, DELETEs rows.
def poll():
    rows = db.execute("SELECT * FROM outbox WHERE sent_at IS NULL LIMIT 50").fetchall()
    for row in rows:
        publish(row.payload)
        db.execute("DELETE FROM outbox WHERE id = ?", row.id)
