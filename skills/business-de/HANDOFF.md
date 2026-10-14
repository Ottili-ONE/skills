# business-de — HANDOFF

What to re-verify, when, and what to build next. Owner: `skills/business-de/**`
(this job: `skills-business-de-r3`). Last full quality pass: 2026-10-14 (PASS 5).

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

## PASS 5 (EVALS + cross-links + handoff) — 2026-10-14

Gate results, re-run 2026-10-14:

| Gate | Command | Result |
|---|---|---|
| 1 | `python3 scripts/validate_skill.py <10 skill dirs>` | 10 ok, 0 issues |
| 2 | `python3 skills/business-de/scripts/run_evals.py` | 74 commands run, 0 failed |
| 3 | `python3 skills/business-de/scripts/audit_triggers_links.py` | 0 problems, graph acyclic, sinks: `gobd-archive` |
| 4 | `python3 -m pytest -q` (per skill) | all suites green |
| 5 | every `references/EVALS.md` has >= 5 prompts + >= 3 near-misses | 10/10 |
| 6 | `skills/business-de/README.md` + `skills/business-de/HANDOFF.md` | both present |

PASS 5 changes: added the missing near-miss prompts (carrier-apis-de +3,
datev-extf +3, dsgvo-ai-act-labeling +3, gobd-archive +3, publish-reconcile-wp-meta +3,
skr-journal-mapping +3, webhooks-safe +3, xrechnung-zugferd +2), re-verified every
version pin in `config/versions.json` against its primary source (recorded in
`config/REVERIFY_2026-10-15.md`), hardened `scripts/common.py` and three scripts
against offline-determinism and edge cases, and rewrote the Related sections as a
downstream-only DAG (audit confirms no cycles).


## PASS 4 (EVALS + cross-links + handoff) — 2026-10-14

Twelve commits, all `skills-business-de-r3-05:`, own paths only.

1. **Trigger + cross-link audit script.** `scripts/audit_triggers_links.py`
   parses every `## Related skills` section, walks the graph and reports
   cycles and trigger gaps (a skill whose body names a sibling but does not
   link it). Result: acyclic, `gobd-archive` is the pure sink, 0 problems.
2. **Live re-verification of every version pin.** All 20 pins in
   `config/versions.json` re-fetched on 2026-10-14; the record is
   `config/REVERIFY_2026-10-14.md`. No pin changed. Two facts remain
   **unverified** and are flagged as such in the skill text: the EU AI Act
   Art. 50 enforcement calendar (eur-lex HTTP 202, empty HTML body) and the
   UStG §13b renumbering (dejure.org HTTP 200, JS-rendered text). Eight
   URLs are still flaky (AO/UStG/BEG 000, iso20022.org/swift.com 403,
   akretion.github.io/steuer-berater.de 404) — corroborated by mirrors.
3. **EVALS grounding pass.** Every `## Run these checks` section in all ten
   `references/EVALS.md` was rewritten so each command is copy-paste-safe,
   runs against a shipped fixture in `<skill>/evals_fixtures/`, and carries
   its expected exit code as a `# exits N` annotation. `run_evals.py` was
   extended to extract commands from fenced ```bash blocks (with backslash
   line-continuations) and to honour per-command exit annotations. Gate:
   **74 commands, 0 failed**.
4. **Bugs found and fixed by running the evals.** Three were real:
   - `recon_check.py` had no IBAN check at all, so EVALS prompt #11 (the
     Bundesbank Pruefzahlenberechnung) was false. Added
     `german_iban_ok()` (DE remainder-1, letters→numbers, country+check
     digits moved to the end) and 8 evals_fixtures.
   - `disclosure_label.py` reported `human_review_status: missing` for a
     transparency-only chatbot that had reviewer id + date (EVALS #5). It
     now reports `approved`; an optional `--evidence` flag was added.
   - `process_register.py` rejected the human-readable `contractual
     necessity` basis that its own EVALS prompt #2 uses. Added
     `LEGAL_BASE_SYNONYMS`; the register still stores the canonical Art. 6
     key. `track.py` non-numeric numbers exit 1, not 0 (the `SystemExit`
     message was correct, the docstring was wrong).
5. **Cross-link audit.** Every `## Related skills` section re-read. The graph
   is acyclic: `gobd-archive` is the pure retention sink and links to nobody;
   every other skill links to it for its retention class. Verified by hand
   and by `audit_triggers_links.py`.
6. **README + this file.** `README.md` rewritten (one-line value per skill,
   install hints, layout diagram, version-pin rule, cross-link contract, gate
   commands) and this file updated.

Gate: `validate_skills.py` → 10 skills, 0 issues. `run_evals.py` → 74
commands, 0 failed. `audit_triggers_links.py` → 0 problems. `pytest` → 216
passed.

Two regressions were found by running the full suite after the grounding
pass and fixed in the same commit: `recon_check.py` had been passing
`sys.argv` (including the script name) to `main()`, so every invocation
read `recon_check.py` as the JSON file and the IBAN check was duplicated
inside `check()` (where it could not be opted out of); `ust_check.py`'s new
`--rows` CLI rejected the positional file form the existing tests pass.
Both are fixed and the suite is green again.

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
