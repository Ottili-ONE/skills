---
# truth:allow-german-file: this wrapper quotes German statute titles and headings verbatim
name: ref-gobd-archive
description: "UNVERIFIED reference wrapper for the GoBD archive skill (business-de/gobd-archive). reviewed_by: UNVERIFIED pending Steuerberater/DPO sign-off in docs/reviews/ref-gobd-archive.md. Not legal/tax advice."
license: MIT-compat
compatibility: "framework-agnostic; German GoBD; offline"
reviewed_by: UNVERIFIED
metadata: {}
allowed-tools: []
---

# ref-gobd-archive — UNVERIFIED

> **Status: UNVERIFIED.** This reference is a sign-off placeholder. It must NOT be quoted
> as certified tax/accounting advice until a Steuerberater/DPO signs
> `docs/reviews/ref-gobd-archive.md` (reviewer name, date and signature). The canonical, runnable implementation
> lives in `skills/business-de/gobd-archive/` (owned by skills-business-de-r3); this wrapper
> only marks the reference for adviser sign-off and records no new legal claims.

## Scope (carried over from the canonical skill, unverified)

- GoBD (Grundsätze zur Ordnungsmäßigkeit der Buchführung und Buchunterlagen) compliance for
  archived accounting records: completeness, readability, traceability, retention periods.
- Evidence classification for tax correspondence (6-year retention for ruling evidence).

## What changed in this wrapper

- `reviewed_by: UNVERIFIED` — the reference is now explicitly marked as not certified.
- Sign-off gate: `python3 scripts/validate_reviewed_by.py` audits this skill. While the
  frontmatter carries the `UNVERIFIED` sentinel the audit reports the skill as unverified
  and exits 0; as soon as the frontmatter names a reviewer, the audit fails unless
  `docs/reviews/ref-gobd-archive.md` carries a filled `Reviewed by:`, `Date:` and
  `Signature:` line.
- No new legal claims are added; the canonical skill's content is not edited here
  (cross-job ownership).

## Related

- Canonical implementation: `skills/business-de/gobd-archive/`
- Sign-off placeholder: `docs/reviews/ref-gobd-archive.md`
