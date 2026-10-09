# Procedures — webhooks-safe

All provider secrets and TTLs are read from `config/versions.json` (never
hardcode). Re-verify each provider's signature scheme before every build and
record the retrieval date in `references/SOURCES.md`.

## 1. Verify the signature over the raw body

Never parse the body first and re-encode it — JSON re-encoding changes byte
order and every signature fails. Read the raw request bytes.

**GitHub** (`X-Hub-Signature-256`):
```python
import hmac, hashlib
expected = "sha256=" + hmac.new(secret, body, hashlib.sha256).hexdigest()
if not hmac.compare_digest(expected, header):
    reject()
```
The header format is `sha256=<hex>`. The older `X-Hub-Signature` (SHA1) is
deprecated — never fall back to it.

**Stripe** (`Stripe-Signature`):
```python
ts, v1 = header.split(",")[0].split("=")[1], header.split(",")[1].split("=")[1]
if abs(now - int(ts)) > REPLAY_WINDOW_SECONDS:
    reject("replay")          # check timestamp BEFORE the HMAC
expected = hmac.new(secret, f"{ts}.{body}".encode(), hashlib.sha256).hexdigest()
if not hmac.compare_digest(expected, v1):
    reject()
```
Stripe's timestamp is part of the signed material. A signature older than
the replay window is a replay attack — reject it before checking the HMAC.

**Always use `hmac.compare_digest`** — a plain `==` is vulnerable to timing
attacks.

## 2. Dedupe

Every webhook carries an event id (GitHub `X-GitHub-Event` + delivery id,
Stripe `id`). Store the id with a TTL in an atomic check-and-set:

| Situation | Action |
|---|---|
| Event id seen, within TTL | Ack and skip; never process twice |
| Event id seen, TTL expired | Re-process (idempotency must still hold) |
| Event id new | Process and store with TTL |

Dedupe must be atomic — a race between check and set processes the event
twice. Use a database `INSERT ... ON CONFLICT DO NOTHING` or a lock.

## 3. Preserve order

Ordering is **per delivery stream, not global**. Two independent providers
can interleave; only enforce order within one stream.

If an event arrives out of sequence, hold it until the missing event arrives
or the replay window expires. Track the highest processed sequence number per
stream. If `seq != last + 1`, buffer.

## 4. Respect replay windows

If a provider guarantees delivery within N minutes, hold unprocessed events
for that window before declaring them lost. Stripe: 5 minutes. GitHub: TTL on
the delivery id (24h default).

## 5. Dead-letter

| Trigger | Action |
|---|---|
| Signature invalid | Reject immediately; do not dead-letter (it is not our event) |
| Processing throws 3 times | Move to dead-letter with raw payload + reason |
| Replay window expired | Move to dead-letter marked "lost" |

Never silently drop a webhook. The dead-letter record must contain the raw
payload, the event id, the failure reason and the timestamp.

## 6. SSRF-safe delivery

If the skill ever needs to deliver outbound, validate the target URL against
an allow-list of Ottili endpoints. Never deliver to arbitrary hosts. An
attacker-controlled webhook payload that triggers an outbound call is an
SSRF.

## 7. Log

Record every verify/dedupe/delivery decision with the event id. The log must
answer: was the signature valid, was this a duplicate, was it delivered.

## 8. Offline helper scripts

- `scripts/verify.py` — verifies a webhook signature against the raw body
  (dry-run by default; `--execute` sends).
- `scripts/dedupe.py` — checks and records an event id with a TTL.
- `scripts/deadletter.py` — moves a failed event to the dead-letter queue.
