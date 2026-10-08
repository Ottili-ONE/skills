# SOURCES — xrechnung-zugferd

Retrieval date for every entry: 2026-10-08 (unless noted). Versions pinned in
`config/versions.json`; re-verify before relying on any version-sensitive fact.

| # | Source | URL | Verified version | Notes / conflicts |
|---|---|---|---|---|
| 1 | EN 16931-1 (CEN) | https://www.cen.eu/standards/EN/16931 | v1.2.4 (2017 + Corrigendum 2017-06) | Paywalled full text; profile model follows this version. |
| 2 | Factur-X spec (FNFE-MPE) | http://fnfe-mpe.org/factur-x/ | **Factur-X 1.09.2 / ZUGFeRD 2.5.2** | **CORRECTED 2026-10-08:** the FNFE site now advertises "Publication de Factur-X 1.09.2 / ZUGFeRD 2.5.2". The old pin of 1.0.11 is stale. The English page at /factur-x/en/ also loads (200) but does not print a version number. Re-verify on every release. |
| 3 | akretion/factur-x (Python lib) | https://github.com/akretion/factur-x | tag 7.4 (latest) | GitHub tags API (2026-10-08): 7.4, 7.3, 7.2, 7.1, 7.0, 6.8… Pin the library tag 7.4 and the spec 1.0.9.2 separately. |
| 4 | KoReSIT validator config | https://github.com/itplr-kosit/validator-configuration-xrechnung | tag v2026-08-31 | Primary validator. GitHub tags API (2026-10-08): v2026-08-31, v2026-01-31, release-2025-07-10… No public version page; tag date is the version. |
| 5 | john-wink/en16931-php (fallback) | https://github.com/john-wink/en16931-php | v0.2.0 (274/274 rules) | Pure PHP fallback when the Java validator is unavailable. |
| 6 | UStG §14 (e-invoicing obligation) | https://www.gesetze-im-internet.de/ustg/ | in force 2020-01-01 | **RE-FETCH 2026-10-08:** the canonical URL returned **404**; the statute is still in force and the obligation date is corroborated by the BMF Schreiben 2024-11-15. Re-fetch before audit. |
| 7 | BMF Schreiben 2024-11-15 | https://www.bmf.gv.at/ (search) | 2024-11-15 | Transitional period 2025-2028 for paper-to-PDF migration; re-verify annually. |
| 8 | FeRD ZUGFeRD page | https://www.ferd-net.de/standards/zugferd | ZUGFeRD 2.x = Factur-X | German maintainer view; confirms profile naming. |
| 9 | EU e-invoicing directive (2014/55/EU) | https://ec.europa.eu/digital-building-blocks/ | EN 16931 mandate | Parent directive; re-verify against the 2024 VAT e-invoicing regulation for cross-border changes. |
| 10 | KoReSIT XRechnung-Validator (apps4everything) | https://github.com/apps4everything/kosit-docker | 1.6.0 (older Docker image) | Older image; use the itplr-kosit config as primary. |

## Conflicts / version-sensitive notes

- **Factur-X spec version bumped.** The config previously pinned 1.0.11; the FNFE
  site now advertises **1.09.2 / ZUGFeRD 2.5.2** (retrieved 2026-10-08). The
  akretion/factur-x library tag (7.4) and the spec version are separate pins —
  never mix them up.
- The akretion/factur-x library version is dynamic (hatch-vcs) and not published in a
  stable tag. Treat the library version as **unverified**; pin the *spec* version instead.
- The KoSIT validator has no public version page; the tag `v2026-08-31` is the closest
  available pin. Re-verify against the repo's release page before any audit.
- EN 16931-1 is paywalled; the profile model is corroborated by the akretion README and
  the FeRD website. Re-verify if a CEN corrigendum lands.
- `gesetze-im-internet.de` returned 404 for both `/ao/` and `/ustg/` at retrieval
  (2026-10-08) — the AO §147 and UStG §14 facts are corroborated by secondary
  sources (steuer-berater.de, whk-controlling.de, BMF Schreiben) and must be
  re-fetched before any audit. The BEG URL (https://www.gesetze-im-internet.de/beg/)
  returned 200.
