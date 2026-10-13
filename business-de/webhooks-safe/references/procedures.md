# Procedures — webhooks-safe

All provider secrets come from config; never hardcode a key in this file or in
scripts.

## 1. Provider signature table

Verified 2026-10-12 against the providers' own docs.

| Provider | Header / field | Algorithm | Secret used | Replay window |
|---|---|---|---|---|
| Meta | `hub.mode=subscribe` GET | token match, no HMAC | `hub.verify_token` | n/a |
| GitHub | `X-Hub-Signature-256` | HMAC-SHA256, prefix `sha256=` | webhook secret | configurable |
| Stripe | `Stripe-Signature` | HMAC-SHA256 over `t,<epoch>,v1` | webhook signing secret | **5 min** |
| Twilio | `X-Twilio-Signature` | HMAC-SHA256 over URL + params + body | auth token | configurable |
| DHL | custom header | HMAC-SHA256 over raw body | webhook secret | configurable |

Stripe's signature input is `t,{epoch_seconds},{v1}` where `t` is the
`timestamp` field from the header. A 5-minute skew is the documented window.

## 2. Handshake (Meta only)

```bash
# GET /webhook?hub.mode=subscribe&hub.verify_token=SECRET&hub.challenge=ABC
# 200 + body "ABC" if token matches, else 403
```

## 3. Signature verification (constant time)

```python
import hmac, hashlib
def verify(provider, raw_body, header_value, secret):
    if provider == "github":
        sig = "sha256=" + hmac.new(secret, raw_body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(sig, header_value)
    if provider == "stripe":
        # header: t=1234567890,v1=abc
        t, v1 = parse(header_value)
        signed = hmac.new(secret, f"{t}.{raw_body}".encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(signed, v1)
    raise ValueError(f"unknown provider {provider}")
```

Never compare with `==`; always `hmac.compare_digest`.

## 4. Replay window

- **Stripe:** reject if `now - event.created > 300` seconds. The event is
  still valid if it arrived late — treat it as a **replay** and re-process
  idempotently, do not discard.
- **GitHub/Meta:** no documented window. Apply a configurable window with a
  hard cap; an out-of-window delivery is a replay, not a rejection.

## 5. Dedup

| State | Action |
|---|---|
| not present | insert pending, process, mark completed |
| present, completed | 200 ack, no side effects |
| present, pending | 202, do not re-run |

The idempotency key is provider-defined: `X-GitHub-Delivery`, Stripe
`event.id`, Meta `entry[i].id`.

## 6. Ordering

Version state per aggregate. If event for aggregate X version 3 arrives
before version 2, buffer version 3 and apply version 2 when it arrives.
Never silently drop.

## 7. Dead-letter

On the Nth consecutive failure, move the event to a dead-letter queue with the
raw payload preserved. A dead-letter entry is never silently retried; it needs
a human decision.

## 8. SSRF-safe forwarding

Any URL an agent is asked to deliver to is DNS-resolved at request time and
blocked if it resolves to private, loopback, link-local or metadata
addresses (169.254.0.0/16, 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16,
127.0.0.0/8, ::1, fc00::/7). Cap redirects at 3.

## Worked examples

### Good — GitHub signature verified

```
X-Hub-Signature-256: sha256=9f86d081...
```
Compute HMAC-SHA256 over the raw body with the webhook secret; the hex digest
matches → 200, process.

### Bad — wrong algorithm assumed

```
X-Hub-Signature-256: sha256=deadbeef
```
A generic agent might skip verification because "the header looks right".
Correct: 401, log, do not process.
