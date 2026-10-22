# Platform integrations guidance — carrier/publish `--execute` removal

Recorded 2026-10-16 by SKL-W1-02. Decision record only; the removal is a cross-job
request (see `docs/gaps/SKL-W1-02.md` X-002).

## Decision

Drop the `--execute` send-paths from the carrier and publish scripts and keep only the
idempotency/reconcile guidance inside the platform integrations docs. Do NOT delete the
skills: they carry the offline validation and near-miss test suites that the platform
lane depends on.

## Verified `--execute` sites (canonical skills, skills-business-de-r3 owned)

| File | Line |
|------|------|
| `skills/business-de/carrier-apis-de/scripts/label_create.py` | 62 (`--execute`), 63 (`--token`), 64 (`--url`), 85 (guard) |
| `skills/business-de/carrier-apis-de/scripts/track.py` | 86 (`--execute`), 87 (`--token`), 88 (`--url`), 109 (dry-run note), 112 (guard) |
| `skills/business-de/publish-reconcile-wp-meta/scripts/meta_publish.py` | 53 (`--execute`), 55 (`--token`), 68 (guard) |
| `skills/business-de/publish-reconcile-wp-meta/scripts/wp_publish.py` | 50 (`--execute`), SKILL.md reference + `--url`/`--user`/`--pass` send path |

## Guidance to keep (moves to platform integrations docs)

- Idempotency: every outbound carrier/publish request carries an idempotency key;
  retries must reuse it (outbox-idempotency rule).
- Reconcile: `scripts/reconcile.py` in both skills compares the platform state to the
  ledger and reports unallocated differences; run it after every send.
- Dry-run by default: scripts build and validate the request without sending; a send is
  an explicit, logged, operator-authorised action.

## Status

**NOT DONE.** The canonical skills are owned by skills-business-de-r3; this job cannot
edit them. Recorded here so the next pass does not re-derive the decision.
