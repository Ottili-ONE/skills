# business-de — HANDOFF

What to re-verify, when, and what to build next. Owner: `skills/business-de/**`
(this job: `skills-business-de-r3`). Last full quality pass: 2026-10-14 (PASS 3).

## Re-verify on every spec bump

| When | What | Where |
|---|---|---|
| Before any audit | Re-fetch every primary source; record HTTP code + date | each `references/SOURCES.md` |
| On validator bump | KoSIT `validator-configuration-xrechnung` tag; EXTF 700/13 | `config/versions.json` |
| On UStG/BEG/AO change | Rates, thresholds, retention classes | `config/versions.json` + `ust-edge-cases/SOURCES.md` |
| On carrier API change | Endpoint paths, idempotency headers, tracking TTL | `carrier-apis-de/SOURCES.md` |
| On webhook provider change | Signature scheme, replay window | `webhooks-safe/SOURCES.md` |

Known flaky URLs (403/404 at 2026-10-09 re-check): `gesetze-im-internet.de/ao/`,
`gesetze-im-internet.de/uStg/`, `iso20022.org/...message-definitons`,
`swift.com/standards`, `akretion.github.io/factur-x/`, `bundesbank.de/...iban`.
Corroborate those facts with the mirrors already recorded before an audit.

## Re-run the gate

```bash
python3 skills/business-de/scripts/validate_skills.py   # must be 0 issues
cd skills/business-de && python3 -m pytest -q           # 216 tests
```
## PASS 3 (DEEPEN) — 2026-10-14

Three commits, all `skills-business-de-r3-01:`, own paths only.

1. **Re-verification of every version-sensitive fact.** Re-fetched 11 primary
   URLs on 2026-10-14. Confirmed: Factur-X 1.09.2 / ZUGFeRD 2.5.2, KoSIT config
   tag v2026-08-31, UStG §14 and §13b via dejure.org, whk-controlling GoBD
   classes. Re-confirmed the two statute portals (`gesetze-im-internet.de/ustg/`
   and `/ao/`) are still 404 — the dejure.org mirrors carry the authoritative
   text. Added a `Re-check 2026-10-14` block to all ten `references/SOURCES.md`
   files. Net effect on pinned versions: none.
2. **Worked good/bad examples added to all ten skills** in
   `references/procedures.md`. Previously five skills had none
   (`gobd-archive`, `dsgvo-ai-act-labeling`, `publish-reconcile-wp-meta`,
   `ust-edge-cases`, `skr-journal-mapping`); the other five had only partial
   coverage. Every skill now has at least two GOOD/BAD pairs covering its
   highest-error-rate operation.
3. **Script hardening.** Two real bugs fixed and caught by new tests:
   - `carrier-apis-de/scripts/track.py` — the live branch built the request
     envelope but then sent the bare base URL, silently dropping the carrier
     tracking path. Now `main()` uses the URL returned by `build_request()`.
   - `webhooks-safe/scripts/verify.py` — PayPal/Twilio verification accepted a
     bare HMAC with no replay window. Now `--now` is required for
     stripe/paypal/twilio and a signature with no timestamp is rejected.
   Added `carrier-apis-de/tests/carrier_test_helpers.py` as an import anchor.

Gate: `validate_skills.py` → 10 skills, 0 issues. `pytest` → 216 passed
(was 212).

## Ideas for the next ten skills (with rationale)

1. **`bank-reconciliation-camt` → MT940 legacy ingest** — most German banks still
   deliver MT940; camt.053 is B2B-only. Rationale: covers the long tail until
   SEPA migration completes.
2. **`carrier-apis-de` → freight-cost allocation** — label cost must land on the
   right cost centre before the journal mapper runs. Rationale: closes the
   carrier → accounting loop.
3. **`webhooks-safe` → idempotency-key registry** — keys need a TTL and a
   collision policy beyond the in-memory dedupe. Rationale: prevents duplicate
   postings across process restarts.
4. **`xrechnung-zugferd` → ZUGFeRD 2.5.2 / Factur-X 1.09.2 migration** — the FNFE-MPE
   page bumped the spec; the pin must follow. Rationale: audit readiness.
5. **`ust-edge-cases` → EU ViDA (2027-01-01)** — OSS, VAT on e-commerce and
   platform liability. Rationale: secondary sources flag it; first to ship wins.
6. **`skr-journal-mapping` → SKR03 support** — GmbH & Co. KG still uses SKR03.
   Rationale: the pin is SKR04-only today.
7. **`dsgvo-ai-act-labeling` → Art. 30 register automation** — turn the manual
   register into a scripted export. Rationale: the procedure is already written.
8. **`datev-extf` → EXTF category 16 (Debitoren/Kreditoren)** — only 21 is built.
   Rationale: AR/AP exports are the next most common DATEV exchange.
9. **`gobd-archive` → immutability proof (WORM/HASH chain)** — retention classes are
   decided; the *proof* of non-alteration is not. Rationale: auditor asks for it.
10. **`publish-reconcile-wp-meta` → multi-site reconciliation** — today it is
    WP-vs-Meta only; the next step is a third platform. Rationale: the field-by-field
    engine generalises cleanly.
