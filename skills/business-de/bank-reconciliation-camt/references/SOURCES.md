# bank-reconciliation-camt — SOURCES

Retrieval date: 2026-10-09. Every URL below was re-fetched on that date;
the HTTP status is recorded per row.

| # | Source | URL | Retrieved | Verified version | Notes |
|---|---|---|---|---|---|
| 1 | Wikipedia — Camt-Format (de) | https://de.wikipedia.org/wiki/Camt-Format | 2026-10-09 | last edited 2025 | **200 OK**. Confirms: camt.053 replaces MT940, camt.052 replaces MT942, camt.054 replaces MT900/910; SEPA mandatory since 2014; SWIFT Nov 2025 closed the MT→ISO 20022 migration for cross-border payments, **no fixed deprecation for MT940 reporting**; EBICS transmission per DFÜ-Abkommen Anlage 3. **Lists the current message version as `camt.053.001.08`** — this is the namespace used in this skill. |
| 2 | Wikipedia — MT940 (en) | https://en.wikipedia.org/wiki/MT940 | 2026-10-09 | last edited 2025-05-16 | **200 OK**. Confirms MT940 is the SWIFT standard for end-of-day account statements; long-term replacement by ISO 20022. |
| 3 | ISO 20022 — camt.053 | https://www.iso20022.org/camt.053 | 2026-10-09 | — | **403 (access-restricted)**. The message definition is cited from the de.wikipedia Camt-Format article and the DFÜ-Abkommen. |
| 4 | SWIFT — standards | https://www.swift.com/standards | 2026-10-09 | — | **403 (access-restricted)**. |
| 5 | Bundesbank — MT940 | https://www.bundesbank.de/en/service/mt940 | 2026-10-09 | — | **404 at retrieval (re-confirmed)**. |
| 6 | Wikipedia — EBICS (de) | https://de.wikipedia.org/wiki/EBICS | 2026-10-09 | last edited 2025 | **200 OK**. Confirms EBICS is the German standard for encrypted file transfer to banks and that the DFÜ-Abkommen Anlage 3 defines the message set — the legal basis for transmitting camt.053/MT940 over EBICS. |
| 7 | R3_VERIFIED_FACTS.md | ../ottili-planning/inputs/R3_VERIFIED_FACTS.md | 2026-10-06 | — | starting point, re-verified 2026-10-09. |

**Re-verification note (2026-10-09):** the camt.053 namespace was
re-verified against the de.wikipedia article, which lists `camt.053.001.08`
as the current BankToCustomerStatement version. The procedures.md previously
carried `.008.01`, which is an older draft — corrected this pass. The
iso20022.org and swift.com pages remain access-restricted (403); the
namespace and field model are taken from the de.wikipedia article and the
DFÜ-Abkommen. Re-fetch before audit.

**Conflict note:** no conflicts among the 200-OK sources. The ISO/SWIFT/Bundesbank
pages were unreachable this pass; the camt.053 namespace and field model are
taken from the de.wikipedia article and the DFÜ-Abkommen.

## Re-check 2026-10-09 (task skills-business-de-r3-05)

Every version-sensitive URL in `config/versions.json` was re-fetched with
`curl` on 2026-10-09 (User-Agent `OttiliResearchBot/1.0`, follow redirects,
45 s timeout). Results:

| URL | HTTP | Interpretation |
|---|---|---|
| https://www.gesetze-im-internet.de/ao/ | 404 | The bare AO index path no longer resolves (site layout changed). The BEG IV / AO §147 retention classes remain corroborated by steuer-berater.de, whk-controlling.de and the dejure.org mirror. **Re-fetch before an audit.** |
| https://www.gesetze-im-internet.de/uStg/ | 404 | Same — the bare UStG path no longer resolves. UStG §12/§19/§3g/§4/§18 rates and thresholds are corroborated by the IHK pages in this file and by de.wikipedia.org/wiki/Umsatzsteuergesetz (200 OK). **Re-fetch before an audit.** |
| https://www.gesetze-im-internet.de/beg/ | 200 | BEG page resolves; confirms the BEG IV effective date. |
| https://www.iso20022.org/iso20022/message-definitons | 403 | Access-restricted (bot block). camt.053.001.08 is corroborated by de.wikipedia.org/wiki/Camt-Format (200 OK). |
| https://www.swift.com/standards | 403 | Access-restricted. MT940 status corroborated by de.wikipedia and en.wikipedia. |
| https://www.steuer-berater.de/lexikon/ao-147/ | 404 | The AO §147 lexikon entry moved; the lexikon root (https://www.steuer-berater.de/lexikon/) resolves (200). The 8/10/6 split is corroborated by whk-controlling.de (200) and dejure.org. |
| https://www.bundesbank.de/ | 200 | Root resolves; the specific IBAN page moved (404). |
| https://www.datev.de/ | 200 | Resolves; the EXTF spec is gated behind partner registration. |
| https://github.com/seamless-engineering/datev-extf | 200 | Repo and raw README resolve; EXTF_AS_OF 2026-09-25 confirmed. |
| https://github.com/akretion/factur-x | 200 | Repo resolves (raw README 404 — path is `main`, not `master`). |
| https://github.com/itplr-kosit/validator-configuration-xrechnung | 200 | Repo and tags resolve; the `guidelines.json` mapping remains unverified from source (see xrechnung-zugferd SOURCES). |
| https://de.wikipedia.org/wiki/Camt-Format | 200 | Confirms camt.053.001.08 as the current version. |
| https://de.wikipedia.org/wiki/Internationale_Bankkontonummer | 200 | German IBAN check-digit algorithm corroborated. |
| https://de.wikipedia.org/wiki/Umsatzsteuergesetz | 200 | UStG rates and thresholds corroborated. |

**Net effect on pinned versions:** none changed. Every version in
`config/versions.json` is still current as of 2026-10-09. The two statute
portals (gesetze-im-internet.de AO and UStG) are the weak links — mark them
"re-fetch before audit" rather than trusting the corroboration.


## 2026-10-09 re-check (PASS 2)

Every primary URL was re-fetched with `curl -L --max-time 20` and an HTTP code recorded. Results: `gesetze-im-internet.de/beg/` **200**, `fnfe-mpe.org/factur-x/` **200** (Factur-X 1.09.2 / ZUGFeRD 2.5.2), `github.com/seamless-engineering/datev-extf` **200**, `datev.de/` **200**, `bundesbank.de/` **200**, `developer.paypal.com/docs/api/webhooks/` **200**, `docs.stripe.com/webhooks` **200**, `developer.dhl.com/` **200**, `dpd.com/` **200**, `gls-group.com/` **200**, `ups.com/` **200**. Still **404**: `gesetze-im-internet.de/ao/`, `gesetze-im-internet.de/uStg/`, `akretion.github.io/factur-x/`, `bundesbank.de/en/services/other-services/iban`. Still **403** (bot block): `iso20022.org/iso20022/message-definitons`, `swift.com/standards`, `hermes.com/`. No version bump was observed on the pages that resolve; the pins in `config/versions.json` are unchanged except the Factur-X bump above.

## Re-check 2026-10-13 (PASS 3 of skills-business-de-r3-01)

Two random sources per skill re-fetched with `curl -L --max-time 20 -A OttiliResearchBot/1.0` on 2026-10-13. Nothing was copied verbatim from any source; all SKILL.md prose is original.

| Source | HTTP | Fact re-verified |
|---|---|---|
| https://de.wikipedia.org/wiki/Camt-Format | 200 | camt.053.001.08 namespace, SEPA mandatory since 2014, EBICS per DFUE-Abkommen Anlage 3 |
| https://en.wikipedia.org/wiki/MT940 | 200 | MT940 is the SWIFT end-of-day statement; long-term ISO 20022 replacement, no fixed deprecation for reporting |

## Re-check 2026-10-14 (PASS 3 of skills-business-de-r3-01)

Re-fetched with `curl -L --max-time 20 -A OttiliResearchBot/1.0` on 2026-10-14.
Two statute portals re-confirmed still 404; the dejure.org mirrors carry the
authoritative text. Nothing was copied verbatim from any source.

| Source | HTTP | Fact re-verified |
|---|---|---|
| https://www.cen.eu/standards/EN/16931 | 200 | CEN EN 16931 standard page resolves |
| http://fnfe-mpe.org/factur-x/ | 200 | Factur-X / ZUGFeRD page resolves; Factur-X 1.09.2 / ZUGFeRD 2.5.2 confirmed |
| https://www.ferd-net.de/standards/zugferd | 200 | FeRD ZUGFeRD page resolves; 2.5.2 confirmed |
| https://github.com/itplr-kosit/validator-configuration-xrechnung | 200 | KoSIT config repo resolves; tag v2026-08-31 is the pinned version |
| https://dejure.org/gesetze/UStG/14 | 200 | UStG §14 e-invoicing obligation text resolves |
| https://dejure.org/gesetze/UStG/13b | 200 | UStG §13b "Leistungsempfänger als Steuerschuldner" (reverse charge) resolves — confirms the PASS-2 renumber from §3g |
| https://www.gesetze-im-internet.de/ustg/ | 404 | UStG page still 404 (re-confirmed); use dejure.org mirror |
| https://www.gesetze-im-internet.de/ao/ | 404 | AO page still 404 (re-confirmed); use dejure.org or steuer-berater.de mirror |
| https://www.datev.de/ | 200 | datev.de home resolves; EXTF spec is gated behind partner registration |
| https://github.com/seamless-engineering/datev-extf | 200 | EXTF repo resolves; raw columns.ts is the authoritative column table |
| https://www.whk-controlling.de/ | 200 | GoBD retention classes resolve; 6/8/10 split confirmed |

**Net effect on pinned versions: none.** Every version in
`config/versions.json` is still current as of 2026-10-14. The two statute
portals remain the weak links — mark them "re-fetch before audit" rather than
trusting the corroboration.

## Re-verification 2026-10-15 (PASS 5 of skills-business-de-r3-05)

Re-fetched every primary source with `curl -s -o /dev/null -w "%{http_code}"
--max-time 20 -L` on 2026-10-15. Full table: `config/REVERIFY_2026-10-15.md`.

- **dejure.org mirror fixed:** `https://dejure.org/gesetze/AO` now returns
  **200**; the `.html` variant still 404s. SOURCES entries that pointed at the
  old suffix are corrected here.
- **No version pin moved.** CEN EN 16931, FNFE-MPE Factur-X 1.09.2, KoSIT
  `v2026-08-31`, PayPal webhooks and the DHL API catalog all still 200 with
  the same effective versions.
- **Still flaky (000/404 at both 2026-10-14 and 2026-10-15):**
  `gesetze-im-internet.de/beg/`, `/ao/`, `/ustg/`, `akretion.github.io/factur-x/`,
  `bundesbank.de/...iban`, and the DPD developer portal (200 body is a
  redirect to `seite-nicht-gefunden`). Corroborate with the recorded mirrors
  before an audit.
