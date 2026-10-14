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
python3 skills/business-de/scripts/run_evals.py         # every EVALS.md script example must exit 0
cd skills/business-de && python3 -m pytest -q           # full pytest suite
```

## PASS 4 (EVALS + cross-links + handoff) — 2026-10-14

Four commits, all `skills-business-de-r3-05:`, own paths only.

1. **README refresh.** `skills/business-de/README.md` rewritten: one-line value
   per skill, install hints, layout diagram, version-pin rule, cross-link
   contract and the gate commands. The old README carried a stale test count
   (131) and no cross-link notes.
2. **EVALS grounding pass.** Every prompt that names a script was re-run
   against the real script in dry-run mode and its expected exit code
   recorded. Two prompts were broken: `skr-journal-mapping` #2/#5/#7 quoted
   `scripts/...` without `python3`, so `run_evals.py` could not extract a
   command; `ust-edge-cases` N1/N2/N3 quoted the bare script name. Both fixed
   and the expected output captured. `carrier-apis-de` N3 was corrected: the
   cent trap is real (12.50 vs 1250 → exit 1) and now states the exact delta.
3. **Cross-link audit.** Every `## Related skills` section re-read. One
   circular edge was found and broken: `dsgvo-ai-act-labeling` linked to
   `webhooks-safe` (which links back). It now links only to `gobd-archive`,
   the retention sink. `gobd-archive` remains a pure sink. Verified acyclic by
   walking the graph by hand.
4. **This file.** Re-verify table, gate commands, and the next-ten list.

Gate: `validate_skills.py` → 10 skills, 0 issues. `run_evals.py` → all
extracted commands exit 0.

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
    WP-vs-Meta only; the next step is a third platform. Rationale: the
    field-by-field engine generalises cleanly.
