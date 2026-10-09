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
    reject()  # replay attack — check BEFORE the HMAC
expected = hmac.new(secret, f"{ts}.".encode() + body, hashlib.sha256).hexdigest()
if not hmac.compare_digest(expected, v1):
    reject()
```
Stripe's timestamp is part of the signature: reject stale signatures *before*
the HMAC check. Window: 5 minutes (pinned in config).

**PayPal / Twilio:** plain HMAC-SHA256 over the raw body, hex digest. Both
schemes are **unverified** at this retrieval — see SOURCES.md. The scripts
fall back to plain HMAC and the skill flags the result.

**Thresholds:** replay window 5 min (Stripe), 24h dedupe TTL; 3 dead-letter
attempts before moving to the queue.

## 2. Dedupe by event id with a TTL

Every webhook carries an event id. Store the id with a TTL; on a duplicate
id, ack and skip. Check-and-set must be atomic — a race that checks then
sets processes the event twice.

```bash
python3 dedupe.py --event-id abc123 --ttl 86400 --store /tmp/events.jsonl
```
Output on duplicate: `{"event_id": "abc123", "duplicate": true, "action": "ack_and_skip"}`.
Output on new: `{"event_id": "abc123", "duplicate": false, "action": "process"}`.

**Good output** (first delivery):
```json
{"event_id": "evt_1", "duplicate": false, "action": "process"}
```
**Bad output** — processing the same id twice:
```json
[{"event_id": "evt_1", "action": "process"}, {"event_id": "evt_1", "action": "process"}]
```
Detect it: two `process` actions for one event id. The dedupe store must show
`duplicate: true` on the second call.

## 3. Preserve per-stream order

Ordering is enforced *within a single delivery stream* (one provider +
one account), never globally. Two independent providers may interleave.

```bash
python3 ordering.py --stream github:ottili --seq 3 --payload body.json --store /tmp/order.jsonl
```
- In order (`seq == last + 1`): process and release any held events that now
  chain.
- Out of order: hold until the gap fills or the replay window expires.
- Old/duplicate (`seq <= last`): ack and skip.

**Good output** (in order):
```json
{"stream": "github:ottili", "action": "process", "seq": 3}
```
**Bad output** — processing seq 5 before seq 4:
```json
{"stream": "github:ottili", "action": "process", "seq": 5}
```
Detect it: `action: process` for a seq that skips the previous one. The state
file must show `last_seq` advancing monotonically.

## 4. Respect replay windows

If a provider guarantees delivery within N minutes, hold unprocessed events
for that window before declaring them lost. For Stripe the timestamp is part
of the signature — reject stale signatures before checking the HMAC.

## 5. Dead-letter

On persistent failure (3 attempts), move the event to the dead-letter queue
with the raw payload, the event id, the failure reason and the timestamp.
Never silently drop a webhook.

```bash
python3 deadletter.py --event-id abc --reason 'timeout' --payload body.json --queue /tmp/dl.jsonl
```
**Good output:**
```json
{"event_id": "abc", "queued": "/tmp/dl.jsonl", "reason": "timeout"}
```
**Bad output** — dropping the event:
```json
{"event_id": "abc", "dropped": true}
```
Detect it: no dead-letter record exists for the failed event id, or the
record lacks the raw payload.

## 6. SSRF-safe delivery

Publish only to the configured Ottili endpoints. Never publish to arbitrary
hosts — an attacker-controlled content field that triggers a publish to an
arbitrary host is an SSRF. Validate the target against the allow-list.

```bash
python3 ssrf_check.py --url https://ottili.example/webhooks/inbound --allow ottili.example
```
- Allow-listed host + path: deliver.
- Allow-listed host, different path: reject.
- Any other host: reject immediately.
- IP literal or `localhost`: reject (never resolve).

## 7. Offline helper scripts

- `scripts/verify.py` — verifies GitHub/Stripe/PayPal/Twilio signatures over
  the raw body (dry-run; reads the body file, never sends).
- `scripts/dedupe.py` — atomic check-and-set on the event id with a TTL.
- `scripts/ordering.py` — per-stream sequence enforcement with a held set and
  replay-window expiry.
- `scripts/deadletter.py` — moves a failed event to the dead-letter queue.
- `scripts/ssrf_check.py` — allow-list validation of outbound delivery targets.
